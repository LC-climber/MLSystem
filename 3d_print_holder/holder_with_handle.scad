// Parametric open-top holder with an angled hollow handle.
// Units: millimeters.

$fn = 48;
eps = 0.05;

// Insert object.
insert_x = 41.0;
insert_y = 41.0;
insert_z = 21.0;

// Fit clearance. Start with 0.6 mm total XY clearance for FDM printing.
clearance_xy = 0.6;
clearance_z = 0.4;

// Holder shell.
wall = 3.0;
bottom = 3.0;

// Handle.
handle_length = 45.0;
handle_width = 22.0;
handle_height = 15.0;
handle_angle_deg = 100.0; // 90 = straight back, 100 = 10 degrees upward.
handle_root_overlap = 2.0;
handle_attach_z_ratio = 0.52;

// Cable channel inside the handle.
cable_channel_width = 10.0;
cable_channel_height = 6.0;

// Mounting holes through the handle. Disable if you will use a clamp instead.
use_mounting_holes = true;
mount_hole_diameter = 3.4; // M3 clearance hole.
mount_hole_spacing_x = 14.0;
mount_hole_distance_from_shell = 34.0;

// Print a small ring first to test whether the real 41 mm part fits.
build_fit_test_ring = false;
fit_test_height = 8.0;

inner_x = insert_x + clearance_xy;
inner_y = insert_y + clearance_xy;
inner_z = insert_z + clearance_z;

outer_x = inner_x + wall * 2;
outer_y = inner_y + wall * 2;
outer_z = inner_z + bottom;

handle_tilt_deg = handle_angle_deg - 90.0;
handle_attach_z = outer_z * handle_attach_z_ratio;

module shell_solid(height = outer_z) {
    translate([-outer_x / 2, -outer_y / 2, 0])
        cube([outer_x, outer_y, height]);
}

module shell_cavity_cut(height = outer_z) {
    translate([-inner_x / 2, -inner_y / 2, bottom])
        cube([inner_x, inner_y, height - bottom + 2 * eps]);
}

module handle_transform() {
    translate([0, -outer_y / 2, handle_attach_z])
        rotate([-handle_tilt_deg, 0, 0])
            children();
}

module handle_solid() {
    handle_transform()
        translate([-handle_width / 2, -handle_length, -handle_height / 2])
            cube([handle_width, handle_length + handle_root_overlap, handle_height]);
}

module cable_channel_cut() {
    handle_transform()
        translate([
            -cable_channel_width / 2,
            -handle_length - eps,
            -cable_channel_height / 2
        ])
            cube([
                cable_channel_width,
                handle_length + handle_root_overlap + 2 * eps,
                cable_channel_height
            ]);
}

module mounting_holes_cut() {
    if (use_mounting_holes) {
        handle_transform() {
            for (x = [-mount_hole_spacing_x / 2, mount_hole_spacing_x / 2]) {
                translate([x, -mount_hole_distance_from_shell, 0])
                    cylinder(h = handle_height + 2 * eps, d = mount_hole_diameter, center = true);
            }
        }
    }
}

module side_ribs() {
    rib_w = 3.0;
    rib_len = 24.0;
    rib_z0 = max(1.0, handle_attach_z - handle_height / 2 - 4.0);
    rib_z1 = min(outer_z, handle_attach_z + handle_height / 2);
    rib_z2 = handle_attach_z - handle_height / 2;
    y0 = -outer_y / 2 + 0.5;
    y1 = -outer_y / 2 - rib_len;

    for (x = [-handle_width / 2 + rib_w / 2, handle_width / 2 - rib_w / 2]) {
        translate([x - rib_w / 2, 0, 0])
            polyhedron(
                points = [
                    [0, y0, rib_z0],
                    [rib_w, y0, rib_z0],
                    [0, y0, rib_z1],
                    [rib_w, y0, rib_z1],
                    [0, y1, rib_z2],
                    [rib_w, y1, rib_z2]
                ],
                faces = [
                    [0, 2, 4],
                    [1, 5, 3],
                    [0, 1, 3, 2],
                    [2, 3, 5, 4],
                    [4, 5, 1, 0]
                ]
            );
    }
}

module full_holder() {
    difference() {
        union() {
            shell_solid();
            handle_solid();
            side_ribs();
        }

        shell_cavity_cut();
        cable_channel_cut();
        mounting_holes_cut();
    }
}

module fit_test_ring() {
    difference() {
        shell_solid(fit_test_height);
        translate([-inner_x / 2, -inner_y / 2, -eps])
            cube([inner_x, inner_y, fit_test_height + 2 * eps]);
    }
}

if (build_fit_test_ring) {
    fit_test_ring();
} else {
    full_holder();
}
