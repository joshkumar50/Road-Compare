"""
YOLOv8 Training Script for Road Safety Detection
Train a custom model on your road infrastructure dataset
"""

import os
import yaml
import argparse
from pathlib import Path
from ultralytics import YOLO
import albumentations as A
from albumentations.pytorch import ToTensorV2
import cv2
import numpy as np

# Data augmentation pipeline for robust training
def get_augmentation_pipeline():
    """Advanced augmentation pipeline for road conditions"""
    return A.Compose([
        # Weather conditions
        A.RandomRain(p=0.3),
        A.RandomFog(fog_coef_lower=0.3, fog_coef_upper=0.5, p=0.3),
        A.RandomSnow(p=0.2),
        
        # Lighting conditions
        A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5),
        A.RandomGamma(p=0.3),
        A.RandomShadow(p=0.3),
        
        # Motion and camera effects
        A.MotionBlur(blur_limit=7, p=0.4),
        A.GaussianBlur(blur_limit=(3, 7), p=0.3),
        A.ImageCompression(quality_lower=60, quality_upper=100, p=0.3),
        
        # Occlusions
        A.CoarseDropout(
            max_holes=3, 
            max_height=50, 
            max_width=50, 
            fill_value=0, 
            p=0.3
        ),
        
        # Geometric transformations
        A.ShiftScaleRotate(
            shift_limit=0.1, 
            scale_limit=0.1, 
            rotate_limit=5, 
            p=0.5
        ),
        
        # Color augmentations
        A.HueSaturationValue(
            hue_shift_limit=10, 
            sat_shift_limit=20, 
            val_shift_limit=20, 
            p=0.3
        ),
        
        # Noise
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.2),
        A.ISONoise(p=0.2),
    ])

def create_dataset_yaml(data_dir: str, output_path: str = "dataset.yaml"):
    """Create YOLO dataset configuration file"""
    
    # Define classes for road safety
    classes = [
        'sign_board',
        'damaged_sign',
        'lane_marking',
        'faded_marking',
        'pothole',
        'longitudinal_crack',
        'transverse_crack',
        'alligator_crack',
        'divider',
        'damaged_divider',
        'guardrail',
        'damaged_guardrail',
        'manhole',
        'speed_bump',
        'zebra_crossing',
        'traffic_light',
        'road_edge',
        'debris',
        'water_pooling',
        'road_patch'
    ]
    
    dataset_config = {
        'path': os.path.abspath(data_dir),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': len(classes),
        'names': classes
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    
    print(f"✅ Dataset config saved to {output_path}")
    return output_path

def prepare_training_data(data_dir: str, augment: bool = True):
    """Prepare and augment training data"""
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Create directory structure
    for split in ['train', 'val', 'test']:
        os.makedirs(f"{data_dir}/images/{split}", exist_ok=True)
        os.makedirs(f"{data_dir}/labels/{split}", exist_ok=True)
    
    if augment:
        print("🔄 Applying data augmentation...")
        augmentor = get_augmentation_pipeline()
        
        # Process training images
        train_dir = f"{data_dir}/images/train"
        for img_file in Path(train_dir).glob("*.jpg"):
            img = cv2.imread(str(img_file))
            
            # Apply augmentation 3 times per image
            for i in range(3):
                augmented = augmentor(image=img)['image']
                new_name = img_file.stem + f"_aug{i}.jpg"
                cv2.imwrite(f"{train_dir}/{new_name}", augmented)
        
        print("✅ Data augmentation complete")

def train_yolov8(
    data_yaml: str,
    model_size: str = 'x',  # n, s, m, l, x
    epochs: int = 300,
    batch_size: int = 16,
    imgsz: int = 640,
    patience: int = 50,
    device: str = 'cuda',
    project_name: str = 'road_safety',
    resume: bool = False
):
    """Train YOLOv8 model with optimal settings for road safety"""
    
    # Select model
    if resume and os.path.exists('runs/detect/road_safety/weights/last.pt'):
        model = YOLO('runs/detect/road_safety/weights/last.pt')
        print("📂 Resuming from checkpoint")
    else:
        model = YOLO(f'yolov8{model_size}.pt')
        print(f"🚀 Starting fresh training with YOLOv8{model_size}")
    
    # Training arguments optimized for road safety detection
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        patience=patience,
        device=device,
        project='runs/detect',
        name=project_name,
        exist_ok=resume,
        
        # Optimization settings
        optimizer='AdamW',  # Better than default SGD for this task
        lr0=0.001,  # Initial learning rate
        lrf=0.01,  # Final learning rate factor
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        
        # Augmentation (additional to albumentations)
        hsv_h=0.015,  # HSV-Hue augmentation
        hsv_s=0.7,    # HSV-Saturation augmentation
        hsv_v=0.4,    # HSV-Value augmentation
        degrees=5.0,  # Rotation
        translate=0.1,  # Translation
        scale=0.2,    # Scaling
        shear=2.0,    # Shear
        flipud=0.0,   # No vertical flip for road images
        fliplr=0.5,   # Horizontal flip
        mosaic=1.0,   # Mosaic augmentation
        mixup=0.2,    # Mixup augmentation
        
        # Loss weights
        box=7.5,      # Box loss weight
        cls=0.5,      # Classification loss weight
        dfl=1.5,      # Distribution focal loss weight
        
        # Other settings
        close_mosaic=20,  # Disable mosaic for last N epochs
        amp=True,     # Automatic mixed precision
        fraction=1.0,  # Dataset fraction
        profile=False,
        freeze=None,   # Freeze layers
        multi_scale=True,  # Multi-scale training
        overlap_mask=True,
        mask_ratio=4,
        dropout=0.0,
        val=True,
        save=True,
        save_period=-1,
        cache=True,    # Cache images for faster training
        workers=8,
        rect=False,
        cos_lr=True,   # Cosine learning rate scheduler
        label_smoothing=0.0,
        plots=True,
        
        # Early stopping
        patience=patience,
        
        # Logging
        verbose=True,
    )
    
    print(f"✅ Training complete! Best model saved to: runs/detect/{project_name}/weights/best.pt")
    
    # Validate the model
    print("\n📊 Running validation...")
    metrics = model.val()
    
    print("\n📈 Key Metrics:")
    print(f"  mAP50: {metrics.box.map50:.3f}")
    print(f"  mAP50-95: {metrics.box.map:.3f}")
    print(f"  Precision: {metrics.box.mp:.3f}")
    print(f"  Recall: {metrics.box.mr:.3f}")
    
    return model

def export_model(model_path: str, formats: list = ['onnx', 'engine']):
    """Export model to different formats for deployment"""
    
    model = YOLO(model_path)
    
    for fmt in formats:
        print(f"\n📦 Exporting to {fmt}...")
        model.export(format=fmt, imgsz=640, simplify=True)
        print(f"✅ Exported to {fmt}")

def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 for Road Safety Detection')
    parser.add_argument('--data-dir', type=str, required=True, 
                        help='Path to dataset directory')
    parser.add_argument('--model-size', type=str, default='x', 
                        choices=['n', 's', 'm', 'l', 'x'],
                        help='Model size: n(ano), s(mall), m(edium), l(arge), x(tra-large)')
    parser.add_argument('--epochs', type=int, default=300,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Batch size for training')
    parser.add_argument('--img-size', type=int, default=640,
                        help='Image size for training')
    parser.add_argument('--device', type=str, default='cuda',
                        help='Device to use: cuda or cpu')
    parser.add_argument('--augment', action='store_true',
                        help='Apply data augmentation')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last checkpoint')
    parser.add_argument('--export', action='store_true',
                        help='Export model after training')
    
    args = parser.parse_args()
    
    print("🛣️ Road Safety Detection - YOLOv8 Training")
    print("=" * 50)
    
    # Prepare data
    if args.augment:
        prepare_training_data(args.data_dir, augment=True)
    
    # Create dataset config
    data_yaml = create_dataset_yaml(args.data_dir)
    
    # Train model
    model = train_yolov8(
        data_yaml=data_yaml,
        model_size=args.model_size,
        epochs=args.epochs,
        batch_size=args.batch_size,
        imgsz=args.img_size,
        device=args.device,
        resume=args.resume
    )
    
    # Export if requested
    if args.export:
        model_path = f'runs/detect/road_safety/weights/best.pt'
        export_model(model_path, formats=['onnx', 'tflite'])
    
    print("\n🎉 Training pipeline complete!")
    print(f"📁 Model saved to: runs/detect/road_safety/weights/best.pt")
    print(f"📁 Copy this file to: backend/app/models/road_defects_yolov8x.pt")

if __name__ == '__main__':
    main()
