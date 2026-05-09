# -*- coding: utf-8 -*-
import torchvision.transforms.functional as TF
import torchvision.transforms as T
import numpy as np
import torch
import random
from torch.utils.data import Dataset
from torchvision import transforms as T
from torchvision.transforms import functional as F
from typing import Callable
import os
import cv2
import Config as config
from typing import Callable, Optional, Tuple, Dict, List
import torch.nn.functional as F
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from torchvision.transforms import InterpolationMode
from bertem import BertEmbeddingWrapper

# Constants
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


# ---------- Utilities ----------
def correct_dims(image: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensure image is HxWxC and mask is HxW (single channel).
    
    Args:
        image: numpy array (H,W,C) or (H,W)
        mask: numpy array (H,W) or (H,W,1)
    
    Returns:
        Tuple of (image, mask) with corrected dimensions
    """
    # Image: if grayscale (H,W) expand to H,W,3 for consistency
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    elif image.ndim == 3 and image.shape[-1] == 1:
        # Single channel, expand to 3 channels
        image = np.repeat(image, 3, axis=-1)
    
    # Mask: ensure HxW (no channel dimension)
    if mask.ndim == 3 and mask.shape[-1] == 1:
        mask = mask[:, :, 0]
    elif mask.ndim == 3:
        # If multi-channel mask, take first channel as binary mask
        mask = mask[:, :, 0]
    
    return image, mask


def sorted_image_mask_pairs(img_dir: str, mask_dir: str) -> Tuple[List[str], List[str]]:
    """
    Return two lists (images_sorted, masks_sorted) matched by filename.
    
    Matching strategy:
    1. Try exact filename match
    2. Try basename match (without extension)
    3. Raise error if no match found
    
    Args:
        img_dir: Directory containing images
        mask_dir: Directory containing masks
    
    Returns:
        Tuple of (image_filenames, mask_filenames) in matched order
    
    Raises:
        FileNotFoundError: If no matching mask found for an image
        ValueError: If directories are empty
    """
    if not os.path.exists(img_dir):
        raise FileNotFoundError(f"Image directory not found: {img_dir}")
    if not os.path.exists(mask_dir):
        raise FileNotFoundError(f"Mask directory not found: {mask_dir}")
    
    imgs = sorted([f for f in os.listdir(img_dir) if not f.startswith('.')])
    masks = sorted([f for f in os.listdir(mask_dir) if not f.startswith('.')])
    
    if len(imgs) == 0:
        raise ValueError(f"No images found in {img_dir}")
    if len(masks) == 0:
        raise ValueError(f"No masks found in {mask_dir}")
    
    # Create lookup maps for different naming patterns
    mask_exact_map = {name: name for name in masks}
    mask_basename_map = {os.path.splitext(name)[0]: name for name in masks}
    
    # For masks with "mask_{imageName}" pattern
    mask_prefix_map = {}
    for mask_name in masks:
        mask_base = os.path.splitext(mask_name)[0]
        # Check if mask name starts with "mask_"
        if mask_base.startswith("mask_"):
            # Extract the original image name after "mask_"
            original_name = mask_base[5:]  # Remove "mask_" prefix
            mask_prefix_map[original_name] = mask_name

    paired_imgs = []
    paired_masks = []

    for im_name in imgs:
        matched = False
        
        # Strategy 1: Try exact match
        if im_name in mask_exact_map:
            paired_imgs.append(im_name)
            paired_masks.append(mask_exact_map[im_name])
            matched = True
            continue
        
        # Strategy 2: Try basename match
        base = os.path.splitext(im_name)[0]
        if base in mask_basename_map:
            paired_imgs.append(im_name)
            paired_masks.append(mask_basename_map[base])
            matched = True
            continue
        
        # Strategy 3: Try "mask_{imageName}" pattern with full filename
        mask_with_prefix = f"mask_{im_name}"
        if mask_with_prefix in mask_exact_map:
            paired_imgs.append(im_name)
            paired_masks.append(mask_exact_map[mask_with_prefix])
            matched = True
            continue
        
        # Strategy 4: Try "mask_{basename}" pattern
        if base in mask_prefix_map:
            paired_imgs.append(im_name)
            paired_masks.append(mask_prefix_map[base])
            matched = True
            continue
        
        # Strategy 5: Try "mask_{basename}" with different extension
        mask_base_with_prefix = f"mask_{base}"
        if mask_base_with_prefix in mask_basename_map:
            paired_imgs.append(im_name)
            paired_masks.append(mask_basename_map[mask_base_with_prefix])
            matched = True
            continue
        
        # No match found - provide helpful error message
        if not matched:
            available_masks = list(mask_basename_map.keys())[:5]  # Show first 5
            raise FileNotFoundError(
                f"No mask file found matching image '{im_name}'\n"
                f"Tried matching strategies:\n"
                f"  1. Exact match: '{im_name}'\n"
                f"  2. Basename match: '{base}'\n"
                f"  3. Prefix match (full): 'mask_{im_name}'\n"
                f"  4. Prefix match (base): 'mask_{base}'\n"
                f"Available mask basenames (first 5): {available_masks}"
            )

    return paired_imgs, paired_masks


# ---------- Transforms ----------
class RandomGenerator:
    """
    Training augmentation and preprocessing pipeline.
    
    Applies:
    - Resizing to target size
    - Random geometric augmentations (rotation, flips)
    - Random intensity augmentations (color jitter, gamma, contrast)
    - ImageNet normalization (for pre-trained models)
    
    Input:
        sample: Dict with keys:
            - 'image': np.ndarray (H,W,C) uint8 or torch.Tensor [C,H,W]
            - 'label': np.ndarray (H,W) uint8 or torch.Tensor [H,W] or [1,H,W]
            - 'text': array-like (any shape)
    
    Output:
        sample: Dict with keys:
            - 'image': torch.Tensor [C,H,W] float32, ImageNet normalized
            - 'label': torch.Tensor [1,H,W] float32, values in {0, 1}
            - 'text': torch.Tensor (same shape as input)
    
    Args:
        output_size: Target (H, W) for resizing
        rotation_angle_range: Max rotation angle in degrees (default: 30)
        apply_color_jitter_prob: Probability of applying color jitter (default: 0.3)
        apply_gamma_prob: Probability of applying gamma adjustment (default: 0.3)
        apply_contrast_prob: Probability of applying contrast adjustment (default: 0.3)
    """
    def __init__(
        self,
        output_size: Tuple[int, int],
        rotation_angle_range: float = 30.0,
        apply_color_jitter_prob: float = 0.3,
        apply_gamma_prob: float = 0.3,
        apply_contrast_prob: float = 0.3
    ):
        self.output_size = output_size
        self.rotation_angle_range = rotation_angle_range
        self.apply_color_jitter_prob = apply_color_jitter_prob
        self.apply_gamma_prob = apply_gamma_prob
        self.apply_contrast_prob = apply_contrast_prob
        
        # ImageNet normalization for pre-trained ConvNeXt
        self.normalize = T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        
        # Reusable color jitter transform (more efficient than creating each time)
        self.color_jitter = T.ColorJitter(
            brightness=0.25,
            contrast=0.25,
            saturation=0.15,
            hue=0.08
        )

    def __call__(self, sample: Dict) -> Dict[str, torch.Tensor]:
        image = sample["image"]
        label = sample["label"]
        text = torch.as_tensor(sample["text"])

        # Convert image to tensor [C,H,W], values in [0,1]
        if not torch.is_tensor(image):
            # TF.to_tensor handles HxWxC numpy uint8 or PIL images
            image = TF.to_tensor(image)  # float [0,1], shape [C,H,W]

        # Convert mask to tensor (integer 0/1)
        if not torch.is_tensor(label):
            label = torch.from_numpy(np.ascontiguousarray(label)).long()
        
        # Ensure mask is [H,W] (no channel dimension)
        while label.ndim > 2:
            if label.shape[0] == 1 or label.shape[-1] == 1:
                label = label.squeeze()
            else:
                # Multi-class mask, keep first class only (adjust as needed)
                label = label[0] if label.ndim == 3 and label.shape[0] > 1 else label
                break

        # Resize both image and mask
        image = TF.resize(image, self.output_size, InterpolationMode.BILINEAR)
        
        # Add channel dimension to mask for resize operation
        if label.ndim == 2:
            label = label.unsqueeze(0)  # [1,H,W]
        label = TF.resize(label, self.output_size, InterpolationMode.NEAREST)

        # --- Geometric Augmentations (applied to both image and mask) ---
        r = random.random()
        
        # 50% probability: Apply rotation + flips
        if r < 0.5:
            # Random 90-degree rotations
            k = random.randint(0, 3)
            image = torch.rot90(image, k, dims=(-2, -1))
            label = torch.rot90(label, k, dims=(-2, -1))

            # Random horizontal flip
            if random.random() < 0.5:
                image = TF.hflip(image)
                label = TF.hflip(label)
            
            # Random vertical flip
            if random.random() < 0.5:
                image = TF.vflip(image)
                label = TF.vflip(label)

        # 25% probability: Apply small random rotation
        elif r < 0.75:
            angle = random.uniform(-self.rotation_angle_range, self.rotation_angle_range)
            image = TF.rotate(image, angle, InterpolationMode.BILINEAR, fill=0)
            label = TF.rotate(label, angle, InterpolationMode.NEAREST, fill=0)

        # --- Intensity Augmentations (applied to image only, BEFORE normalization) ---
        
        # Color jitter (brightness, contrast, saturation, hue)
        if random.random() < self.apply_color_jitter_prob:
            image = self.color_jitter(image)
        
        # Gamma adjustment (simulates different exposure)
        if random.random() < self.apply_gamma_prob:
            gamma = random.uniform(0.8, 1.2)
            image = TF.adjust_gamma(image, gamma=gamma)
        
        # Contrast adjustment
        if random.random() < self.apply_contrast_prob:
            contrast_factor = random.uniform(0.9, 1.1)
            image = TF.adjust_contrast(image, contrast_factor)

        # --- Apply ImageNet Normalization (image only, NOT mask) ---
        image = self.normalize(image)

        # Convert mask to float (values remain 0/1)
        label = label.float()

        return {"image": image, "label": label, "text": text}


class ValGenerator:
    """
    Validation/test preprocessing pipeline (deterministic, no augmentation).
    
    Applies:
    - Resizing to target size
    - ImageNet normalization
    
    Input/Output format same as RandomGenerator.
    
    Args:
        output_size: Target (H, W) for resizing
    """
    def __init__(self, output_size: Tuple[int, int]):
        self.output_size = output_size
        self.normalize = T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)

    def __call__(self, sample: Dict) -> Dict[str, torch.Tensor]:
        image = sample["image"]
        label = sample["label"]
        text = torch.as_tensor(sample["text"])

        # Convert to tensors
        if not torch.is_tensor(image):
            image = TF.to_tensor(image)

        if not torch.is_tensor(label):
            label = torch.from_numpy(np.ascontiguousarray(label)).long()

        # Ensure mask is [H,W]
        while label.ndim > 2:
            if label.shape[0] == 1 or label.shape[-1] == 1:
                label = label.squeeze()
            else:
                label = label[0] if label.ndim == 3 and label.shape[0] > 1 else label
                break

        # Resize
        image = TF.resize(image, self.output_size, InterpolationMode.BILINEAR)
        
        if label.ndim == 2:
            label = label.unsqueeze(0)
        label = TF.resize(label, self.output_size, InterpolationMode.NEAREST)

        # Apply ImageNet normalization (image only)
        image = self.normalize(image)

        return {"image": image, "label": label.float(), "text": text}


# ---------- Dataset ----------
class ImageToImage2D(Dataset):
    """
    Dataset for 2D medical image segmentation with optional text embeddings.
    
    Expected directory structure:
        dataset_path/
            img/           # RGB images (PNG/JPG)
            labelcol/      # Grayscale masks
    
    Features:
    - Automatically converts OpenCV BGR to RGB
    - Robust image-mask pairing (handles different extensions)
    - Optional BERT text embeddings
    - Configurable text token length with padding/truncation
    - Optional one-hot encoding for multi-class segmentation
    
    Args:
        dataset_path: Root directory containing 'img' and 'labelcol' subdirectories
        row_text: Dictionary mapping mask_filename -> text description
        joint_transform: Transform object (RandomGenerator or ValGenerator)
        one_hot_mask: Number of classes for one-hot encoding (0 = disabled)
        image_size: Initial resize before transforms (default: 224)
        max_text_tokens: Maximum number of text tokens to use (default: 10)
        text_embed_dim: Dimension of text embeddings (default: 768 for BERT)
        bert_embedding_module: Optional BERT wrapper module path for import
    """
    def __init__(
        self,
        dataset_path: str,
        row_text: str,
        joint_transform: Optional[Callable] = None,
        one_hot_mask: int = False,
        image_size: int = 224,
        max_text_tokens: int = 80,
        text_embed_dim: int = 768
    ):
        self.dataset_path = dataset_path
        self.image_size = image_size
        self.max_text_tokens = max_text_tokens
        self.text_embed_dim = text_embed_dim
        
        # Validate paths
        self.input_path = os.path.join(dataset_path, "img")
        self.output_path = os.path.join(dataset_path, "labelcol")
        
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Image directory not found: {self.input_path}")
        if not os.path.exists(self.output_path):
            raise FileNotFoundError(f"Mask directory not found: {self.output_path}")

        # Robust pairing: sort and match by exact filename or basename
        self.images_list, self.mask_list = sorted_image_mask_pairs(
            self.input_path, 
            self.output_path
        )

        self.one_hot_mask = one_hot_mask if one_hot_mask else 0
        self.rowtext = row_text
        self.joint_transform = joint_transform
        
        # Initialize BERT embedding wrapper
        self.bert_embedding = BertEmbeddingWrapper()
        # Create default transform if none provided
        if self.joint_transform is None:
            print("Warning: No transform provided, using ValGenerator as default")
            self.joint_transform = ValGenerator(output_size=(image_size, image_size))

    def __len__(self) -> int:
        return len(self.images_list)

    def _load_and_process_text(self, mask_filename: str) -> np.ndarray:
        """
        Load and process text embeddings for a given mask filename.
        
        Returns:
            np.ndarray of shape (max_text_tokens, text_embed_dim)
        """
        # Get text description
        text = self.rowtext[mask_filename]
        text = text.split('\n')
        # if config.mode == 'train':
        #     text_tok = get_embeddings(mask_filename)
        # else:
        #     # text_tok = self.bert_embedding(text)
        #     pass
        text_tok = self.bert_embedding(text)
        text_arr = np.array(text_tok[0][1])  # Assuming this is the embedding array
        
        # Truncate or pad to max_text_tokens
        if text_arr.shape[0] > self.max_text_tokens:
            text_arr = text_arr[:self.max_text_tokens, :]
        elif text_arr.shape[0] < self.max_text_tokens:
            pad_size = self.max_text_tokens - text_arr.shape[0]
            padding = np.zeros((pad_size, self.text_embed_dim), dtype=text_arr.dtype)
            text_arr = np.vstack([text_arr, padding])
        
        return text_arr

    def __getitem__(self, idx: int) -> Tuple[Dict[str, torch.Tensor], str]:
        """
        Get a single sample.
        
        Returns:
            Tuple of (sample_dict, image_filename) where sample_dict contains:
                - 'image': torch.Tensor [C,H,W]
                - 'label': torch.Tensor [1,H,W] or [num_classes,H,W] if one_hot
                - 'text': torch.Tensor [max_text_tokens, text_embed_dim]
        """
        image_filename = self.images_list[idx]
        mask_filename = self.mask_list[idx]

        image_path = os.path.join(self.input_path, image_filename)
        mask_path = os.path.join(self.output_path, mask_filename)

        # Load image (OpenCV loads in BGR format)
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        
        # CRITICAL: Convert BGR to RGB for ImageNet pre-trained models
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Note: We do NOT resize here - let transforms handle it to avoid double resizing
        # This allows transforms to work with original resolution if needed

        # Load mask (grayscale)
        mask = cv2.imread(mask_path, 0)
        if mask is None:
            raise FileNotFoundError(f"Cannot read mask: {mask_path}")

        # Binarize mask: 0 = background, 1 = foreground
        mask = (mask > 0).astype(np.uint8)

        # Ensure correct dimensions: image HxWxC, mask HxW
        image, mask = correct_dims(image, mask)

        # Load and process text embeddings
        text_arr = self._load_and_process_text(mask_filename)

        # Create sample dictionary
        sample = {"image": image, "label": mask, "text": text_arr}

        # Apply transforms (converts to tensors, applies augmentation and normalization)
        if self.joint_transform:
            sample = self.joint_transform(sample)

        # Apply one-hot encoding if requested (AFTER transforms)
        if self.one_hot_mask and self.one_hot_mask > 0:
            lbl = sample["label"]  # [1,H,W] float
            
            # Remove channel dimension and convert to long
            if lbl.ndim == 3 and lbl.shape[0] == 1:
                lbl = lbl.squeeze(0)  # [H,W]
            lbl = lbl.long()
            
            # Ensure values are in valid range
            if lbl.max() >= self.one_hot_mask:
                raise ValueError(
                    f"Mask contains class {lbl.max()} but one_hot_mask={self.one_hot_mask}"
                )
            
            # Convert to one-hot: [H,W] -> [num_classes,H,W]
            oh = F.one_hot(lbl, num_classes=self.one_hot_mask)  # [H,W,C]
            oh = oh.permute(2, 0, 1).float()  # [C,H,W]
            sample["label"] = oh

        return sample, image_filename


# ---------- Convenience Functions ----------
def create_train_dataloader(
    dataset_path: str,
    row_text: Dict[str, str],
    batch_size: int = 8,
    num_workers: int = 4,
    image_size: int = 224,
    **dataset_kwargs
) -> torch.utils.data.DataLoader:
    """
    Convenience function to create training DataLoader.
    
    Args:
        dataset_path: Path to dataset root
        row_text: Dictionary of text descriptions
        batch_size: Batch size
        num_workers: Number of workers for data loading
        image_size: Image size
        **dataset_kwargs: Additional arguments for ImageToImage2D
    
    Returns:
        DataLoader for training
    """
    train_transform = RandomGenerator(output_size=(image_size, image_size))
    dataset = ImageToImage2D(
        dataset_path=dataset_path,
        row_text=row_text,
        joint_transform=train_transform,
        image_size=image_size,
        **dataset_kwargs
    )
    
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True  # Important for batch normalization
    )


def create_val_dataloader(
    dataset_path: str,
    row_text: Dict[str, str],
    batch_size: int = 8,
    num_workers: int = 4,
    image_size: int = 224,
    **dataset_kwargs
) -> torch.utils.data.DataLoader:
    """
    Convenience function to create validation DataLoader.
    
    Args:
        dataset_path: Path to dataset root
        row_text: Dictionary of text descriptions
        batch_size: Batch size
        num_workers: Number of workers for data loading
        image_size: Image size
        **dataset_kwargs: Additional arguments for ImageToImage2D
    
    Returns:
        DataLoader for validation
    """
    val_transform = ValGenerator(output_size=(image_size, image_size))
    dataset = ImageToImage2D(
        dataset_path=dataset_path,
        row_text=row_text,
        joint_transform=val_transform,
        image_size=image_size,
        **dataset_kwargs
    )
    
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False
    )
