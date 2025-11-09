# 📘 Visualization Repository

## Visualization

## Installation

### Installation Prerequisites

Conda should be installed and data should be acquired using Data_Acquisition project

### Clone the Repository
```bash
git clone https://github.com/iarvanitis69/phd_visualization.git
cd phd_visualization
```

### Activate Basic Conda Commands

1. Change directory
```bash
cd phd_preprocessing
```

2. Activate Conda environment
```bash
   conda activate phd_cond_env_p10
```
---

## Execute Preprocessing
```base
python main.py <mseed file>
```

## Visualization tasks
With the help of this repository, we can visualize anything that needs to be displayed as part of the project we are 
referring to—namely, GreensonNet and its results.
In the first phase, what has been implemented is the ability to display msync files, and in fact, to interact with them:
that is, to zoom into specific regions, perform panning, and normalize the signal. This is the initial functionality. 
Additional features will follow in the next stages.