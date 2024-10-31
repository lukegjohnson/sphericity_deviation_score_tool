# sphericity_deviation_score_tool

Simple GUI tool to measure the sphericity deviation score (SDS) from radiographs. 

## Background

SDS is a continuous measure of radiographic residual hip deformity caused by Legg-Calvé-Perthes Disease. The background and a more detailed description of this measure can be found in these papers: [The Sphericity Deviation Score: A Quantitative Radiologic Outcome Measure of Legg-Calvé Perthes Disease Applicable at the Stage of Healing and at Skeletal Maturity](doi.org/10.1097/BPO.0000000000000170) and [Quantitative measures for evaluating the radiographic outcome of Legg-Calvé-Perthes disease](doi.org/10.2106/JBJS.L.00172)

Measuring SDS typically involves drawing and measuring circles in a vector graphics editor such as Adobe Illustrator, and then calculating the final result in a spreadsheet. This project provides a lightweight, intuitive and self-contained GUI tool to measure SDS. After loading radiograph images, the user only needs to place 8 landmarks for the SDS calculation.

## Running the SDS tool

Executable files for Windows and Mac are provided for click-and-go running. 

```source/main.py``` can also be run with Python 3, with the following dependencies installable via ```pip```: ```FreeSimpleGui```, ```numpy```, ```pillow```, and ```pyperclip```

## Using the SDS tool

Running the tool opens 3 windows. Two windows look like this, one each for marking up the AP (anterior-posterior) and lateral views: 

![Screenshot of an image window for the SDS tool](https://github.com/lukegjohnson/sphericity_deviation_score_tool/blob/main/image/window_1.png?raw=true)

To load a radiograph image, use the "Browse" button to point the tool to the correct image, then click "Load image" to load it onto the window. Toggle the "Move" button to drag the image around so the hip is in view, and use "Zoom in/out" to ensure it fills the window before placing your landmarks. 

The last window looks like this:

![Screenshot of the calculations window for the SDS tool](https://github.com/lukegjohnson/sphericity_deviation_score_tool/blob/main/image/window_2.png?raw=true)

When enough landmarks are placed on each image, the tool calculates relevant intermediate measurements (for example, radius of the maximum inscribed circle on the AP view) and the final value of SDS. The row can be copied to the clipboard as tab-separated numbers using "Copy to Clipboard", ready to paste into Excel.
