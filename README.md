# HISM_Support

* Based on work by ```Ganonmaster```
    * https://github.com/Ganonmaster/Blender-Scripts/tree/master/ue4map-tools

## Description

This is a support tool derived from ```ue4map-tools```, designed as a Blender addon that allows you to easily duplicate and position imported HISM instances based on their original Blueprint references.

### How it works

* Get ```InstancedStaticMeshComponent``` and extract its ```TransformData```
* Retrieve the ```Rotation``` ```Translation``` ```Scale3D``` parameters
* For each ```TransformData``` entry, duplicate the base object and apply its position, rotation, and scale accordingly

### Important!
Please make sure to use ```map_mesh_import.py``` from ```ue4map-tools``` first, and uncomment ```InstancedStaticMeshComponent``` before importing.
Only after that should you run this script.

## How to Use

* For usage instructions, please refer to:
    * https://youtu.be/9mho7nr0WOY?si=lMvk9tGq39TOcOin

### Supported Blender Version

* Tested and developed for Blender ```3.4.0```

## Version History

* ```1.0```
    * Initial Release
