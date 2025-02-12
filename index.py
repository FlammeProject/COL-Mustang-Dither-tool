import sys
import numpy as np
import cv2
from PIL import Image, ImageQt, ImageEnhance
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QSlider, QWidget, QComboBox, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QWheelEvent

class DitherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scaleFactor = 1.0  # Facteur de zoom
        self.original_image = None  # Store the original image
        self.additionalSliders = {}  # Store additional sliders for each mode
    
    def initUI(self):
        self.setWindowTitle("Dither Editor")
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
        self.comboDither.addItems(["Floyd-Steinberg", "Bayer 2x2", "Bayer 4x4", "Aléatoire", "Ordered Dithering"])
        self.comboDither.currentIndexChanged.connect(self.updateSliders)
        self.layout.addWidget(self.comboDither)
        
        self.slidersLayout = QHBoxLayout()
        
        self.sliderIntensity = self.createSlider("Intensité", 1, 255, 128)
        self.sliderThreshold = self.createSlider("Seuil", 0, 255, 128)
        self.sliderContrast = self.createSlider("Contraste", 0, 3, 1, 1)
        
        self.slidersLayout.addWidget(self.sliderIntensity[1])
        self.slidersLayout.addWidget(self.sliderThreshold[1])
        self.slidersLayout.addWidget(self.sliderContrast[1])
        
        self.layout.addLayout(self.slidersLayout)
        
        self.btnSave = QPushButton("Enregistrer l'image")
        self.btnSave.clicked.connect(self.saveImage)
        self.layout.addWidget(self.btnSave)
        
        self.setLayout(self.layout)
        self.image = None
    
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
        delta = event.angleDelta().y()
        factor = 1.2 if delta > 0 else 0.8
        self.scaleFactor *= factor
        self.displayImage()
    
    def loadImage(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Ouvrir une image", "", "Images (*.png *.jpg *.bmp)")
        if filePath:
            self.original_image = Image.open(filePath).convert("L")  # Store the original image
            self.image = self.original_image.copy()  # Work on a copy of the original image
            self.displayImage()
    
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
    
    def applyDither(self):
        if self.original_image is None:
            return
        
        method = self.comboDither.currentText()
        intensity = self.sliderIntensity[0].value()
        threshold = self.sliderThreshold[0].value()
        contrast = self.sliderContrast[0].value()
        
        self.image = self.original_image.copy().convert('L')  # Reset to the original image
        enhancer = ImageEnhance.Contrast(self.image)
        self.image = enhancer.enhance(contrast).convert('L')
        image_array = np.array(self.image)
        
        if method == "Floyd-Steinberg":
            self.image = self.image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        elif method == "Bayer 2x2":
            gamma = self.additionalSliders["Gamma"][0].value()
            self.image = Image.fromarray(self.bayerDither(image_array, 2, threshold, gamma))
        elif method == "Bayer 4x4":
            gamma = self.additionalSliders["Gamma"][0].value()
            self.image = Image.fromarray(self.bayerDither(image_array, 4, threshold, gamma))
        elif method == "Aléatoire":
            seed = self.additionalSliders["Seed"][0].value()
            np.random.seed(seed)
            noise = np.random.randint(-intensity, intensity, image_array.shape)
            dithered = np.clip(image_array + noise, 0, 255)
            self.image = Image.fromarray(dithered.astype(np.uint8))
        elif method == "Ordered Dithering":
            matrix_size = self.additionalSliders["Matrix Size"][0].value()
            self.image = Image.fromarray(self.orderedDither(image_array, threshold, matrix_size))
        
        self.displayImage()
    
    def bayerDither(self, img, size, threshold, gamma=1.0):
        threshold_map = np.array([[0, 2], [3, 1]]) * (255 // 4) if size == 2 else \
                         np.array([[0,  8,  2, 10],
                                   [12, 4, 14, 6],
                                   [3, 11, 1,  9],
                                   [15, 7, 13, 5]]) * (255 // 16)
        h, w = img.shape
        tile_h = (h + size - 1) // size
        tile_w = (w + size - 1) // size
        threshold_map = np.tile(threshold_map, (tile_h, tile_w))[:h, :w]
        img = np.power(img / 255.0, gamma) * 255  # Apply gamma correction
        return ((img > (threshold_map + (threshold - 128))) * 255).astype(np.uint8)
    
    def orderedDither(self, img, threshold, matrix_size=4):
        # Create a Bayer matrix of the given size
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
        
        h, w = img.shape
        tile_h = (h + matrix_size - 1) // matrix_size
        tile_w = (w + matrix_size - 1) // matrix_size
        threshold_map = np.tile(bayer_matrix, (tile_h, tile_w))[:h, :w]
        
        return ((img > (threshold_map + (threshold - 128))) * 255).astype(np.uint8)
    
    def displayImage(self):
        if self.image:
            qtImage = ImageQt.ImageQt(self.image)
            pixmap = QPixmap.fromImage(qtImage)
            scaled_pixmap = pixmap.scaled(int(pixmap.width() * self.scaleFactor), int(pixmap.height() * self.scaleFactor), Qt.AspectRatioMode.KeepAspectRatio)
            self.label.setPixmap(scaled_pixmap)
    
    def saveImage(self):
        if self.image:
            filePath, _ = QFileDialog.getSaveFileName(self, "Enregistrer l'image", "", "PNG Files (*.png)")
            if filePath:
                self.image.save(filePath)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DitherApp()
    window.show()
    sys.exit(app.exec())
