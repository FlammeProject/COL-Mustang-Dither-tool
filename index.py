import sys
import numpy as np
import cv2
from PIL import Image, ImageQt
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
        
        self.sliderIntensity = self.createSlider("Intensité")
        self.sliderThreshold = self.createSlider("Seuil")
        self.sliderContrast = self.createSlider("Contraste")
        
        self.slidersLayout.addWidget(self.sliderIntensity[1])
        self.slidersLayout.addWidget(self.sliderThreshold[1])
        self.slidersLayout.addWidget(self.sliderContrast[1])
        
        self.layout.addLayout(self.slidersLayout)
        
        self.btnSave = QPushButton("Enregistrer l'image")
        self.btnSave.clicked.connect(self.saveImage)
        self.layout.addWidget(self.btnSave)
        
        self.setLayout(self.layout)
        self.image = None
    
    def createSlider(self, name):
        container = QWidget()
        layout = QVBoxLayout()
        label = QLabel(name)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(255)
        slider.setValue(128)
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
        
        if method == "Floyd-Steinberg":
            self.image = self.image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        elif method == "Bayer 2x2":
            self.image = Image.fromarray(self.bayerDither(np.array(self.image), 2))
        elif method == "Bayer 4x4":
            self.image = Image.fromarray(self.bayerDither(np.array(self.image), 4))
        elif method == "Aléatoire":
            image_array = np.array(self.image)
            dithered = (image_array + np.random.randint(-intensity, intensity, image_array.shape)).clip(0, 255)
            self.image = Image.fromarray(dithered.astype(np.uint8))
        elif method == "Ordered Dithering":
            self.image = Image.fromarray(self.orderedDither(np.array(self.image)))
        
        self.displayImage()
    
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