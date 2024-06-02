from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
from tensorflow.keras.applications.efficientnet import preprocess_input
import numpy as np

class FeatureExtractor:
    def __init__(self):
        # Load EfficientNetB0 model pre-trained on ImageNet dataset
        base_model = EfficientNetB0(weights='imagenet', include_top=False)
        # Remove the last few layers to extract features directly from the convolutional layers
        self.model = Model(inputs=base_model.input, outputs=base_model.get_layer('top_activation').output)

    def extract(self, img):
        """
        Extract a deep feature from an input image
        Args:
            img: from PIL.Image.open(path) or tensorflow.keras.preprocessing.image.load_img(path)

        Returns:
            feature (np.ndarray): deep feature with the shape=(1280, )
        """
        # Resize the image to the input size required by EfficientNetB0
        img = img.resize((224, 224))
        # Convert PIL image to numpy array
        x = image.img_to_array(img)
        # Add batch dimension
        x = np.expand_dims(x, axis=0)
        # Preprocess input (normalize pixel values)
        x = preprocess_input(x)
        # Extract features from the model
        features = self.model.predict(x)
        # Reshape to 1D array
        feature = features.flatten()
        # Normalize feature vector
        return feature / np.linalg.norm(feature)
