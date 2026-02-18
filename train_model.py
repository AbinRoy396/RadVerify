"""
Model Training Script for RadVerify
Fine-tunes EfficientNet-B0 on fetal ultrasound datasets.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import yaml

try:
    from modules.ai_analyzer import AIAnalyzer
    STRUCTURE_LABELS = [
        f"{category}/{structure}"
        for category, structures in AIAnalyzer.FETAL_STRUCTURES.items()
        for structure in structures
    ]
except Exception:
    STRUCTURE_LABELS = []

class FetalUltrasoundTrainer:
    """Trainer for fine-tuning on medical ultrasound data."""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize trainer with configuration."""
        self.config = self._load_config(config_path)
        self.model = None
        self.history = None
        
    def _load_config(self, config_path):
        """Load training configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}
    
    def build_model(self, num_classes=10):
        """
        Build the fine-tuning model.
        
        Args:
            num_classes: Number of fetal structure classes to detect
        """
        print("Building model for fine-tuning...")
        
        # Load pre-trained EfficientNet-B0
        base_model = EfficientNetB0(
            weights='imagenet',
            include_top=False,
            input_shape=(224, 224, 3)
        )
        
        # Freeze early layers (transfer learning)
        for layer in base_model.layers[:-20]:
            layer.trainable = False
        
        # Add custom classification head
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.3)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.2)(x)
        predictions = Dense(num_classes, activation='softmax')(x)
        
        self.model = Model(inputs=base_model.input, outputs=predictions)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )
        
        print(f"OK: Model built with {num_classes} output classes")
        return self.model
    
    def prepare_data_generators(self, train_dir, val_dir, batch_size=32):
        """
        Create data generators with augmentation.
        
        Args:
            train_dir: Path to training images (organized in class folders)
            val_dir: Path to validation images
            batch_size: Batch size for training
        """
        # Training data augmentation (critical for medical imaging)
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=15,
            width_shift_range=0.1,
            height_shift_range=0.1,
            shear_range=0.1,
            zoom_range=0.1,
            horizontal_flip=True,
            fill_mode='nearest'
        )
        
        # Validation data (no augmentation)
        val_datagen = ImageDataGenerator(rescale=1./255)
        
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(224, 224),
            batch_size=batch_size,
            class_mode='categorical'
        )
        
        val_generator = val_datagen.flow_from_directory(
            val_dir,
            target_size=(224, 224),
            batch_size=batch_size,
            class_mode='categorical'
        )
        
        return train_generator, val_generator
    
    def train(self, train_generator, val_generator, epochs=50, output_dir="models", labels=None):
        """
        Train the model.
        
        Args:
            train_generator: Training data generator
            val_generator: Validation data generator
            epochs: Number of training epochs
            output_dir: Directory to save model weights
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Callbacks
        callbacks = [
            ModelCheckpoint(
                filepath=os.path.join(output_dir, 'best_model.h5'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            ),
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
        
        print(f"\nStarting training for {epochs} epochs...")
        print(f"Training samples: {train_generator.samples}")
        print(f"Validation samples: {val_generator.samples}")
        
        self.history = self.model.fit(
            train_generator,
            validation_data=val_generator,
            epochs=epochs,
            callbacks=callbacks,
            verbose=1
        )
        
        if labels:
            labels_path = os.path.join(output_dir, "labels.json")
            with open(labels_path, "w", encoding="utf-8") as f:
                json.dump(labels, f, indent=2)
            print(f"Saved labels to {labels_path}")

        # Save final model
        final_path = os.path.join(output_dir, 'final_model.h5')
        self.model.save(final_path)
        print(f"\nOK: Training complete! Model saved to {final_path}")
        
        return self.history
    
    def evaluate(self, test_generator):
        """Evaluate model on test set."""
        print("\nEvaluating model...")
        results = self.model.evaluate(test_generator, verbose=1)
        print(f"Test Loss: {results[0]:.4f}")
        print(f"Test Accuracy: {results[1]:.4f}")
        return results


def main():
    """
    Main training pipeline.
    
    USAGE:
    1. Organize your dataset:
       data/
         train/
           class_0_head/
             image1.jpg
             image2.jpg
           class_1_abdomen/
             ...
         val/
           class_0_head/
           class_1_abdomen/
    
    2. Run: python train_model.py
    """
    
    # Configuration for User's Custom Dataset
    # Structure based on screenshot:
    # data/Data/
    #   train/
    #   test/
    #   validation/
    
    # Path to where you extracted the folder
    DATASET_PATH = "data/Data" 
    
    # Explicit folder paths from your screenshot
    TRAIN_DIR = os.path.join(DATASET_PATH, "train")
    VAL_DIR = os.path.join(DATASET_PATH, "validation")
    TEST_DIR = os.path.join(DATASET_PATH, "test")
    
    labels = []
    # Check if we need to auto-detect classes
    if os.path.exists(TRAIN_DIR):
        classes = [d for d in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, d))]
        NUM_CLASSES = len(classes)
        labels = sorted(classes)
        print(f"Detected {NUM_CLASSES} classes: {labels}")
    else:
        NUM_CLASSES = len(STRUCTURE_LABELS) if STRUCTURE_LABELS else 2
        labels = STRUCTURE_LABELS
        
    EPOCHS = int(os.getenv("RADVERIFY_EPOCHS", "20"))
    BATCH_SIZE = int(os.getenv("RADVERIFY_BATCH_SIZE", "16"))

    # Initialize trainer
    trainer = FetalUltrasoundTrainer()
    
    # Build model
    trainer.build_model(num_classes=NUM_CLASSES)
    
    # Prepare data
    print("\nLoading dataset from:", DATASET_PATH)
    
    # Training Generator (from 'train' folder)
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    train_gen = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(224, 224),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )
    
    # Validation Generator (from 'validation' folder)
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    val_gen = val_datagen.flow_from_directory(
        VAL_DIR,
        target_size=(224, 224),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )
    
    # Train
    trainer.train(train_gen, val_gen, epochs=EPOCHS, labels=labels)
    
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("1. Copy 'models/best_model.h5' to your project")
    print("2. Update ai_analyzer.py to load this model:")
    print("   self.model = tf.keras.models.load_model('models/best_model.h5')")
    print("="*50)


if __name__ == "__main__":
    main()
