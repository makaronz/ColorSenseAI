import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Tuple
from database.operations import get_latest_readings
from database.schema import SensorReading

class RealTimeVisualizer:
    def __init__(self):
        # Utworzenie okna Tkinter
        self.root = tk.Tk()
        self.root.title("ColorSense - Wizualizacja w czasie rzeczywistym")
        
        # Konfiguracja wykresu
        self.fig = plt.figure(figsize=(15, 10))
        self.fig.subplots_adjust(hspace=0.5)
        
        # Utworzenie subplotów
        self.ax1 = self.fig.add_subplot(221)  # CCT
        self.ax2 = self.fig.add_subplot(222)  # Luminancja
        self.ax3 = self.fig.add_subplot(223)  # Spektrum
        self.ax4 = self.fig.add_subplot(224)  # Temperatura
        
        # Inicjalizacja danych
        self.timestamps: List[datetime] = []
        self.cct_values: List[float] = []
        self.lux_values: List[float] = []
        self.spectrum_values: Dict[str, List[float]] = {
            '450nm': [], '500nm': [], '550nm': [],
            '570nm': [], '600nm': [], '650nm': []
        }
        self.temp_values: List[float] = []
        
        # Dodanie wykresu do Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
    def update_plots(self, frame):
        """Aktualizacja wykresów."""
        # Pobierz najnowsze odczyty
        readings = get_latest_readings(100)
        
        # Aktualizacja danych
        self.timestamps = [r.timestamp for r in readings]
        self.cct_values = [r.sen0611_cct for r in readings]
        self.lux_values = [r.tsl2591_lux for r in readings]
        self.temp_values = [r.as7262_temperature for r in readings]
        
        for wavelength in self.spectrum_values.keys():
            self.spectrum_values[wavelength] = [
                getattr(r, f'as7262_{wavelength}') for r in readings
            ]
        
        # Czyszczenie wykresów
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # Wykres CCT
        self.ax1.plot(self.timestamps, self.cct_values, 'b-')
        self.ax1.set_title('Temperatura barwowa (CCT)')
        self.ax1.set_ylabel('Temperatura [K]')
        self.ax1.tick_params(axis='x', rotation=45)
        
        # Wykres luminancji
        self.ax2.plot(self.timestamps, self.lux_values, 'g-')
        self.ax2.set_title('Luminancja')
        self.ax2.set_ylabel('Lux')
        self.ax2.tick_params(axis='x', rotation=45)
        
        # Wykres spektrum
        wavelengths = list(self.spectrum_values.keys())
        latest_spectrum = [self.spectrum_values[w][-1] if self.spectrum_values[w] else 0 
                         for w in wavelengths]
        self.ax3.bar(wavelengths, latest_spectrum)
        self.ax3.set_title('Aktualne spektrum')
        self.ax3.set_ylabel('Intensywność')
        
        # Wykres temperatury
        self.ax4.plot(self.timestamps, self.temp_values, 'r-')
        self.ax4.set_title('Temperatura czujnika')
        self.ax4.set_ylabel('Temperatura [°C]')
        self.ax4.tick_params(axis='x', rotation=45)
        
        # Dostosowanie układu
        self.fig.tight_layout()
    
    def start(self):
        """Uruchomienie wizualizacji."""
        # Animacja z odświeżaniem co 1 sekundę
        self.ani = animation.FuncAnimation(
            self.fig, self.update_plots, interval=1000
        )
        self.root.mainloop()
    
    def stop(self):
        """Zatrzymanie wizualizacji."""
        self.root.quit()
        self.root.destroy()

def main():
    """Funkcja główna."""
    visualizer = RealTimeVisualizer()
    try:
        visualizer.start()
    except KeyboardInterrupt:
        visualizer.stop()

if __name__ == "__main__":
    main() 