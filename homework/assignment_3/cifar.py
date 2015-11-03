import pickle
import skimage
import numpy as np

def load_cifar10(filename):
    """
    Loads a single batch of CIFAR images (10,000) from the given `filename`.

    In the CIFAR distribution, the color channels are placed as blocks
    within each image, meaning that all red pixels come before the green pixels
    which again are placed before the blue pixels. 
    
    The images returned from this function are converted to the channel-interleaved representation, 
    where the red, green, and blue channels for a single pixel are next to each other.
    """
    side_len = 32 # Square images of side length `side_len` 
    n_pixels_per_image = side_len * side_len
    with open(filename, 'rb') as f:
        cifar = pickle.load(f, encoding='bytes')
        # Change binary keys to string keys
        cifar = {str(key, encoding='ascii'): val for key, val in cifar.items()}

        images_rgb_in_blocks = skimage.img_as_float(cifar['data'])
        
        n_images = images_rgb_in_blocks.shape[0]
        n_channels = 3
        n_pixels_per_image = side_len * side_len
        
        images_rgb = np.zeros(n_images * n_pixels_per_image * n_channels)
        
        for channel_i in range(n_channels):
            channel = images_rgb_in_blocks.T[channel_i*n_pixels_per_image:(channel_i+1)*n_pixels_per_image]
            images_rgb[channel_i::n_channels] = channel.T.ravel()
            
        cifar['data'] = images_rgb.reshape(n_images, side_len, side_len, n_channels)
        
        return cifar['data'], cifar['labels']