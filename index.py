import sys
import numpy as np
import cv2
from PIL import Image, ImageQt, ImageEnhance
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QSlider, QWidget, QComboBox, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class DitherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
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
        self.comboDither.currentIndexChanged.connect(self.applyDither)
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
        slider.setMinimum(minVal)
        slider.setMaximum(maxVal)
        slider.setValue(defaultVal)
        slider.setSingleStep(int(step))
        slider.valueChanged.connect(self.applyDither)
        layout.addWidget(label)
        layout.addWidget(slider)
        container.setLayout(layout)
        return slider, container
    
    def loadImage(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Ouvrir une image", "", "Images (*.png *.jpg *.bmp)")
        if filePath:
            self.image = Image.open(filePath).convert("L")
            self.displayImage()
    
    def applyDither(self):
        if self.image is None:
            return
        
        method = self.comboDither.currentText()
        intensity = self.sliderIntensity[0].value()
        threshold = self.sliderThreshold[0].value()
        contrast = self.sliderContrast[0].value()
        
        self.image = self.image.convert('L')
        enhancer = ImageEnhance.Contrast(self.image)
        self.image = enhancer.enhance(contrast).convert('L')
        image_array = np.array(self.image)
        
        if method == "Floyd-Steinberg":
            self.image = self.image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        elif method == "Bayer 2x2":
            self.image = Image.fromarray(self.bayerDither(image_array, 2, threshold))
        elif method == "Bayer 4x4":
            self.image = Image.fromarray(self.bayerDither(image_array, 4, threshold))
        elif method == "Aléatoire":
            noise = np.random.randint(-intensity, intensity, image_array.shape)
            dithered = np.clip(image_array + noise, 0, 255)
            self.image = Image.fromarray(dithered.astype(np.uint8))
        elif method == "Ordered Dithering":
            self.image = Image.fromarray(self.orderedDither(image_array, threshold))
        
        self.displayImage()
    
    def bayerDither(self, img, size, threshold):
        threshold_map = np.array([[0, 2], [3, 1]]) * (255 // 4) if size == 2 else \
                         np.array([[0,  8,  2, 10],
                                   [12, 4, 14, 6],
                                   [3, 11, 1,  9],
                                   [15, 7, 13, 5]]) * (255 // 16)
        h, w = img.shape
        tile_h = (h + size - 1) // size
        tile_w = (w + size - 1) // size
        threshold_map = np.tile(threshold_map, (tile_h, tile_w))[:h, :w]
        return ((img > (threshold_map + threshold)) * 255).astype(np.uint8)
    
    def displayImage(self):
        qtImage = ImageQt.ImageQt(self.image)
        pixmap = QPixmap.fromImage(qtImage)
        pixmap = pixmap.scaled(self.scrollArea.width(), self.scrollArea.height(), Qt.AspectRatioMode.KeepAspectRatio)
        self.label.setPixmap(pixmap)
    
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
