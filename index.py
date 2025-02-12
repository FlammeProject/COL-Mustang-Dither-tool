import sys
import numpy as  np
import cv2
from PIL import Image, ImageQt, ImageEnhance
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QSlider, QWidget, QComboBox, QScrollArea
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QWheelEvent
import traceback

class DitherApp(QWidget):
    def __init__(self):
        super().__init__()
        print("Initializing DitherApp...")
        self.initUI()
        self.scaleFactor = 1.0  # Facteur de zoom
        self.original_image = None  # Store the original image
        self.additionalSliders = {}  # Store additional sliders for each mode
        self.image = None  # Initialize self.image
        print("DitherApp initialized.")
    
    def initUI(self):
        self.setWindowTitle("COL Mustang - Dithering")
        self.setGeometry(100, 100, 800, 600)
        
        self.layout = QVBoxLayout()
        
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.label = QLabel("Chargez une image")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scrollArea.setWidget(self.label)
        self.layout.addWidget(self.scrollArea)
        
        self.btnLoad = QPushButton("Charger une Image")
        self.btnLoad.clicked.connect(self.loadImage)
        self.layout.addWidget(self.btnLoad)
        
        self.comboDither = QComboBox()
        self.comboDither.addItems(["Pixel Art", "Bayer 2x2", "Bayer 4x4", "Aléatoire", "Ordered Dithering", "Jarvis-Judice-Ninke", "Stucki", "Burkes"])
        self.comboDither.currentIndexChanged.connect(self.updateSliders)
        self.layout.addWidget(self.comboDither)
        
        self.slidersLayout = QHBoxLayout()
        
        self.sliderIntensity = self.createSlider("Intensité", 1, 255, 128)
        self.sliderThreshold = self.createSlider("Seuil", 0, 255, 128)
        self.sliderContrast = self.createSlider("Contraste", 0, 3, 1, 1)
        self.sliderColorDepth = self.createSlider("Color Depth", 2, 32, 8, 2)
        
        self.slidersLayout.addWidget(self.sliderIntensity[1])
        self.slidersLayout.addWidget(self.sliderThreshold[1])
        self.slidersLayout.addWidget(self.sliderContrast[1])
        self.slidersLayout.addWidget(self.sliderColorDepth[1])
        
        self.layout.addLayout(self.slidersLayout)
        
        self.btnSave = QPushButton("Enregistrer l'image")
        self.btnSave.clicked.connect(self.saveImage)
        self.layout.addWidget(self.btnSave)
        
        self.setLayout(self.layout)
        self.image = None
        self.scrollArea.resizeEvent = self.onResize  # Connect resize event to custom handler
    
    def createSlider(self, name, minVal, maxVal, defaultVal, step=1):
        container = QWidget()
        layout = QVBoxLayout()
        label = QLabel(name)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(int(minVal))
        slider.setMaximum(int(maxVal))
        slider.setValue(int(defaultVal))
        slider.setSingleStep(int(step))
        slider.valueChanged.connect(self.applyDither)
        layout.addWidget(label)
        layout.addWidget(slider)
        container.setLayout(layout)
        return slider, container
    
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.2 if delta > 0 else 0.8
            self.scaleFactor *= factor
            
            # Get the position of the mouse relative to the label
            mouse_pos = event.position()
            label_pos = self.label.mapFromGlobal(self.mapToGlobal(mouse_pos.toPoint()))
            
            # Calculate the new scroll position to keep the zoom centered
            scroll_bar_h = self.scrollArea.horizontalScrollBar()
            scroll_bar_v = self.scrollArea.verticalScrollBar()
            new_h_value = int(label_pos.x() * factor - self.scrollArea.viewport().width() / 2)
            new_v_value = int(label_pos.y() * factor - self.scrollArea.viewport().height() / 2)
            
            self.displayImage()
            
            # Set the new scroll position
            scroll_bar_h.setValue(new_h_value)
            scroll_bar_v.setValue(new_v_value)
        else:
            super().wheelEvent(event)
    
    def loadImage(self):
        try:
            print("Loading image...")
            filePath, _ = QFileDialog.getOpenFileName(self, "Ouvrir une image", "", "Images (*.png *.jpg *.bmp)")
            if filePath:
                print(f"Image path: {filePath}")
                self.original_image = Image.open(filePath).convert("RGB")  # Ensure the image is in RGB format
                print(f"Original image size: {self.original_image.size}")
                self.original_image = self.resizeImage(self.original_image, 1920, 1080)  # Resize if necessary
                print(f"Resized image size: {self.original_image.size}")
                self.image = self.original_image.copy()  # Work on a copy of the original image
                self.displayImage()
                print("Image loaded successfully.")
            else:
                print("No file selected.")
        except Exception as e:
            print(f"Error loading image: {e}")
            traceback.print_exc()

    def resizeImage(self, image, max_width, max_height):
        try:
            width, height = image.size
            if width > max_width or height > max_height:
                scaling_factor = min(max_width / width, max_height / height)
                new_size = (int(width * scaling_factor), int(height * scaling_factor))
                print(f"Resizing image to: {new_size}")
                return image.resize(new_size, Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            print(f"Error resizing image: {e}")
            traceback.print_exc()
            return image
    
    def updateSliders(self):
        method = self.comboDither.currentText()
        for slider in self.additionalSliders.values():
            slider[1].setParent(None)  # Remove existing additional sliders
        
        self.additionalSliders.clear()
        
        if method == "Bayer 2x2" or method == "Bayer 4x4":
            sliderGamma = self.createSlider("Gamma", 0.1, 5.0, 1.0, 0.1)
            self.slidersLayout.addWidget(sliderGamma[1])
            self.additionalSliders["Gamma"] = sliderGamma
        elif method == "Aléatoire":
            sliderSeed = self.createSlider("Seed", 0, 100, 42)
            self.slidersLayout.addWidget(sliderSeed[1])
            self.additionalSliders["Seed"] = sliderSeed
        elif method == "Ordered Dithering":
            sliderMatrixSize = self.createSlider("Matrix Size", 2, 8, 4)
            self.slidersLayout.addWidget(sliderMatrixSize[1])
            self.additionalSliders["Matrix Size"] = sliderMatrixSize
        elif method == "Pixel Art":
            sliderPixelSize = self.createSlider("Pixel Size", 1, 20, 10)
            self.slidersLayout.addWidget(sliderPixelSize[1])
            self.additionalSliders["Pixel Size"] = sliderPixelSize
    
    def applyDither(self):
        try:
            print("Applying dither...")
            if self.original_image is None:
                print("No image loaded.")
                return
            
            method = self.comboDither.currentText()
            intensity = self.sliderIntensity[0].value()
            threshold = self.sliderThreshold[0].value()
            contrast = self.sliderContrast[0].value()
            color_depth = self.sliderColorDepth[0].value()
            
            print(f"Method: {method}, Intensity: {intensity}, Threshold: {threshold}, Contrast: {contrast}, Color Depth: {color_depth}")
            
            self.image = self.original_image.copy()  # Reset to the original image
            enhancer = ImageEnhance.Contrast(self.image)
            self.image = enhancer.enhance(contrast)
            image_array = np.array(self.image)
            
            print("Image array shape:", image_array.shape)
            
            # Apply color depth compression using original image colors
            image_array = self.compressColors(image_array, color_depth)
            
            if method == "Pixel Art":
                if "Pixel Size" in self.additionalSliders:
                    pixel_size = self.additionalSliders["Pixel Size"][0].value()
                    self.image = Image.fromarray(self.pixelArtDither(image_array, pixel_size))
                    self.displayImage()
            elif method == "Bayer 2x2":
                gamma = self.additionalSliders["Gamma"][0].value()
                self.image = Image.fromarray(self.bayerDither(image_array, 2, threshold, gamma))
                self.displayImage()
            elif method == "Bayer 4x4":
                gamma = self.additionalSliders["Gamma"][0].value()
                self.image = Image.fromarray(self.bayerDither(image_array, 4, threshold, gamma))
                self.displayImage()
            elif method == "Aléatoire":
                seed = self.additionalSliders["Seed"][0].value()
                np.random.seed(seed)
                noise = np.random.randint(-intensity, intensity, image_array.shape)
                dithered = np.clip(image_array + noise, 0, 255)
                self.image = Image.fromarray(dithered.astype(np.uint8))
                self.displayImage()
            elif method == "Ordered Dithering":
                matrix_size = self.additionalSliders["Matrix Size"][0].value()
                self.image = Image.fromarray(self.orderedDither(image_array, threshold, matrix_size))
                self.displayImage()
            elif method in ["Jarvis-Judice-Ninke", "Stucki", "Burkes"]:
                self.worker = DitherWorker(image_array, threshold, method)
                self.worker.update_image.connect(self.updateImage)
                self.worker.start()
            print("Dither applied successfully.")
        except Exception as e:
            print(f"Error applying dither: {e}")
            traceback.print_exc()

    def compressColors(self, img, bits):
        if bits < 4 or bits > 32:
            raise ValueError("Color depth must be between 4 and 32 bits.")
        levels = 2 ** bits
        factor = 256 // levels
        img = (img // factor) * factor
        return img

    def updateImage(self, dithered_image):
        self.image = Image.fromarray(dithered_image)
        self.displayImage()
    
    def bayerDither(self, img, size, threshold, gamma=1.0):
        threshold_map = np.array([[0, 2], [3, 1]]) * (255 // 4) if size == 2 else \
                         np.array([[0,  8,  2, 10],
                                   [12, 4, 14, 6],
                                   [3, 11, 1,  9],
                                   [15, 7, 13, 5]]) * (255 // 16)
        h, w, c = img.shape
        tile_h = (h + size - 1) // size
        tile_w = (w + size - 1) // size
        threshold_map = np.tile(threshold_map, (tile_h, tile_w))[:h, :w]
        dithered_img = np.zeros_like(img)
        for channel in range(c):
            channel_img = img[:, :, channel]
            channel_img = np.power(channel_img / 255.0, gamma) * 255  # Apply gamma correction
            dithered_img[:, :, channel] = ((channel_img > (threshold_map + (threshold - 128))) * 255).astype(np.uint8)
        return dithered_img

    def orderedDither(self, img, threshold, matrix_size=4):
        def create_bayer_matrix(n):
            if n == 1:
                return np.array([[0]])
            else:
                smaller_matrix = create_bayer_matrix(n // 2)
                top_left = 4 * smaller_matrix
                top_right = 4 * smaller_matrix + 2
                bottom_left = 4 * smaller_matrix + 3
                bottom_right = 4 * smaller_matrix + 1
                top = np.concatenate((top_left, top_right), axis=1)
                bottom = np.concatenate((bottom_left, bottom_right), axis=1)
                return np.concatenate((top, bottom), axis=0)
        
        bayer_matrix = create_bayer_matrix(matrix_size)
        bayer_matrix = bayer_matrix * (255 // (matrix_size * matrix_size))
        
        h, w, c = img.shape
        tile_h = (h + matrix_size - 1) // matrix_size
        tile_w = (w + matrix_size - 1) // matrix_size
        threshold_map = np.tile(bayer_matrix, (tile_h, tile_w))[:h, :w]
        dithered_img = np.zeros_like(img)
        for channel in range(c):
            channel_img = img[:, :, channel]
            dithered_img[:, :, channel] = ((channel_img > (threshold_map[:h, :w] + (threshold - 128))) * 255).astype(np.uint8)
        return dithered_img

    def errorDiffusionDither(self, img, threshold, method):
        if method == "Floyd-Steinberg":
            kernel = np.array([[0, 0, 7],
                               [3, 5, 1]]) / 16
        elif method == "JJN":
            kernel = np.array([[0, 0, 0, 7, 5],
                               [3, 5, 7, 5, 3],
                               [1, 3, 5, 3, 1]]) / 48
        elif method == "Stucki":
            kernel = np.array([[0, 0, 0, 8, 4],
                               [2, 4, 8, 4, 2],
                               [1, 2, 4, 2, 1]]) / 42
        elif method == "Burkes":
            kernel = np.array([[0, 0, 0, 8, 4],
                               [2, 4, 8, 4, 2]]) / 32
        else:
            raise ValueError(f"Unknown dithering method: {method}")
        
        h, w, c = img.shape
        dithered_img = np.zeros_like(img)
        for channel in range(c):
            channel_img = img[:, :, channel].astype(np.float32)
            for y in range(h):
                for x in range(w):
                    old_pixel = channel_img[y, x]
                    new_pixel = 255 if old_pixel > threshold else 0
                    channel_img[y, x] = new_pixel
                    error = old_pixel - new_pixel
                    for ky in range(kernel.shape[0]):
                        for kx in range(kernel.shape[1]):
                            ny, nx = y + ky, x + kx - 1
                            if 0 <= ny < h and 0 <= nx < w:
                                channel_img[ny, nx] += error * kernel[ky, kx]
            dithered_img[:, :, channel] = channel_img.astype(np.uint8)
        return dithered_img
    
    def pixelArtDither(self, img, pixel_size):
        h, w, c = img.shape
        dithered_img = np.zeros_like(img)
        for y in range(0, h, pixel_size):
            for x in range(0, w, pixel_size):
                block = img[y:y+pixel_size, x:x+pixel_size]
                avg_color = block.mean(axis=(0, 1)).astype(int)
                dithered_img[y:y+pixel_size, x:x+pixel_size] = avg_color
        return dithered_img
    
    def displayImage(self):
        try:
            print("Displaying image...")
            if self.image:
                qtImage = ImageQt.ImageQt(self.image)
                pixmap = QPixmap.fromImage(qtImage)
                scaled_pixmap = pixmap.scaled(self.scrollArea.viewport().size() * self.scaleFactor, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.label.setPixmap(scaled_pixmap)
                self.label.adjustSize()  # Adjust the label size to fit the pixmap
                print("Image displayed.")
            else:
                print("No image to display.")
        except Exception as e:
            print(f"Error displaying image: {e}")
            traceback.print_exc()
    
    def onResize(self, event):
        self.displayImage()
        event.accept()
    
    def saveImage(self):
        try:
            if self.image:
                filePath, _ = QFileDialog.getSaveFileName(self, "Enregistrer l'image", "", "PNG Files (*.png)")
                if filePath:
                    self.image.save(filePath)
        except Exception as e:
            print(f"Error saving image: {e}")
            traceback.print_exc()

class DitherWorker(QThread):
    update_image = pyqtSignal(np.ndarray)

    def __init__(self, image_array, threshold, method):
        super().__init__()
        self.image_array = image_array
        self.threshold = threshold
        self.method = method

    def run(self):
        try:
            dithered_image = self.errorDiffusionDither(self.image_array, self.threshold, self.method)
            self.update_image.emit(dithered_image)
        except Exception as e:
            print(f"Error in DitherWorker: {e}")
            traceback.print_exc()

    def errorDiffusionDither(self, img, threshold, method):
        if method == "JJN":
            kernel = np.array([[0, 0, 0, 7, 5],
                               [3, 5, 7, 5, 3],
                               [1, 3, 5, 3, 1]]) / 48
        elif method == "Stucki":
            kernel = np.array([[0, 0, 0, 8, 4],
                               [2, 4, 8, 4, 2],
                               [1, 2, 4, 2, 1]]) / 42
        elif method == "Burkes":
            kernel = np.array([[0, 0, 0, 8, 4],
                               [2, 4, 8, 4, 2]]) / 32
        else:
            raise ValueError(f"Unknown dithering method: {method}")

        h, w, c = img.shape
        dithered_img = np.zeros_like(img)
        for channel in range(c):
            channel_img = img[:, :, channel].astype(np.float32)
            for y in range(h):
                for x in range(w):
                    old_pixel = channel_img[y, x]
                    new_pixel = 255 if old_pixel > threshold else 0
                    channel_img[y, x] = new_pixel
                    error = old_pixel - new_pixel
                    for ky in range(kernel.shape[0]):
                        for kx in range(kernel.shape[1]):
                            ny, nx = y + ky, x + kx - 2
                            if 0 <= ny < h and 0 <= nx < w:
                                channel_img[ny, nx] += error * kernel[ky, kx]
            dithered_img[:, :, channel] = channel_img.astype(np.uint8)
        return dithered_img

if __name__ == "__main__":
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        window = DitherApp()
        window.show()
        print("Application started.")
        app.exec()  # Keep the application running
        print("Application running.")
    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()
    finally:
        print("Application closed.")