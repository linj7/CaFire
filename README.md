## Calcium Mini Analysis

Calcium mini analysis is a software developed in Python that allows users to analyze calcium imaging mini event data through an interactive graphical user interface, identifying miniature calcium events and calculating corresponding baselines, rise times, amplitudes and decay times.

## Functionalities

- Calculate baseline
- Calculate Amplitude 
- Calculate rise time and decay time
- Export these statistics

## Compile Into EXE

```cmd
pip install pyinstaller
pyinstaller -w -F -i assets/ecg_icon.ico --add-data "assets;assets" calcium_mini_analysis.py
```

