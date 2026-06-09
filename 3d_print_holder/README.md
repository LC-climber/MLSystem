# 41 mm Insert Holder With Angled Hollow Handle

## Scope

This folder contains a parametric OpenSCAD model for an open-top 3D printed holder. It is sized for an insert object measured at `41 mm x 41 mm x 21 mm`, with a rear handle angled around `100 deg` and a hollow cable channel inside the handle.

## Current Design Assumptions

- Insert object: `41 x 41 x 21 mm`.
- Internal cavity: `41.6 x 41.6 x 21.4 mm`.
- Wall thickness: `3 mm`.
- Bottom thickness: `3 mm`.
- Holder outer size before handle: about `47.6 x 47.6 x 24.4 mm`.
- Handle: `45 mm` long, `22 mm` wide, `15 mm` high.
- Handle angle: `100 deg`, interpreted as `10 deg` upward from a straight rear handle.
- Cable channel: `10 x 6 mm`.
- Mounting holes: two M3 clearance holes, `3.4 mm` diameter, `14 mm` apart.

Adjust these values at the top of `holder_with_handle.scad`.

## Environment Checklist

- Caliper for measuring the real insert and cable bundle.
- CAD/model generator: OpenSCAD.
- Slicer: PrusaSlicer or Cura.
- Filament:
  - PLA for fit tests.
  - PETG for the final mechanical part.
  - ABS/ASA only if the printer and workspace can handle enclosure, fumes, and temperature.
- FDM printer with a known nozzle size, usually `0.4 mm`.
- Printer profile in the slicer.

## Ubuntu Installation Commands

Preferred user-level Flatpak route:

```bash
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.openscad.OpenSCAD com.prusa3d.PrusaSlicer
```

System apt route, if you prefer native packages:

```bash
sudo apt update
sudo apt install openscad prusa-slicer
```

## Generate STL

Open the model:

```bash
flatpak run org.openscad.OpenSCAD 3d_print_holder/holder_with_handle.scad
```

Export from GUI: press `F6` to render, then export as STL.

Command-line export, if the Flatpak exposes OpenSCAD CLI correctly:

```bash
flatpak run org.openscad.OpenSCAD -o 3d_print_holder/holder_with_handle.stl 3d_print_holder/holder_with_handle.scad
```

## Fit Test

Before printing the full part, edit `holder_with_handle.scad`:

```scad
build_fit_test_ring = true;
```

Export and print that small ring first. The real insert should enter without force. If it is tight, increase `clearance_xy` from `0.6` to `0.8` or `1.0`.

After the fit test passes, set:

```scad
build_fit_test_ring = false;
```

Then export and print the full part.

## Slicer Settings

- Orientation: top opening faces upward.
- Layer height: `0.2 mm`.
- Perimeters/walls: `4`.
- Top/bottom layers: `5`.
- Infill: `35%` for PETG final part, `20%` for PLA fit test.
- Supports: normally off. Enable only if your slicer shows unsupported handle underside problems.
- Brim: optional, useful for PETG or if the handle causes bed adhesion risk.

## Print And Assembly Steps

1. Measure the real insert, cable bundle, and mechanical mounting screw positions.
2. Update the parameters at the top of `holder_with_handle.scad`.
3. Export and print the fit-test ring.
4. Adjust `clearance_xy` until the insert fits reliably.
5. Export the full holder.
6. Slice with PETG final settings.
7. Print the holder with the top opening upward.
8. Clean stringing and hole edges.
9. Test cable routing through the handle.
10. Mount to the mechanism with M3 screws or revise the mounting-hole parameters.

## Open Items To Confirm

- Exact printer model and nozzle size.
- Screw type and hole spacing on the mechanical device.
- Cable diameter or cable-bundle width.
- Whether the insert needs retention clips, friction fit, or adhesive.
