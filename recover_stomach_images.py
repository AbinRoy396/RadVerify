import os
import shutil

def find_and_move_images():
    src_base = r'C:\Users\abinr\RadVerify\data\datasets\stomach_dataset'
    dst_dir = r'C:\Users\abinr\RadVerify\data\structure_dataset\train\organs_stomach'
    
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    count = 0
    # Use Long Path aware walk if on Windows
    # But for now just normal os.walk should work if we are careful
    for root, dirs, files in os.walk(src_base):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                src_path = os.path.join(root, file)
                # Avoid moving if it's already in the destination name format (unlikely here)
                dst_path = os.path.join(dst_dir, file)
                
                # If file exists, rename it
                base, ext = os.path.splitext(file)
                i = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(dst_dir, f"{base}_{i}{ext}")
                    i += 1
                
                try:
                    shutil.copy2(src_path, dst_path)
                    count += 1
                except Exception as e:
                    print(f"Error copying {src_path}: {e}")
                    
    print(f"Successfully moved {count} images to {dst_dir}")

if __name__ == "__main__":
    find_and_move_images()
