# Pavement and Course Materials

## Scale

**Dimensions:** 16.30 × 9.7 × 1

## Surface Roughness

*Applies only to `Roughplane.blend`.*

Adds subtle surface noise to simulate the natural roughness of pavement.

| Setting | Value |
| --- | --- |
| Slice count | 100 |
| Texture type | Distorted Noise |
| Amount | 10 |
| Size | 0.3 |
| Nabla | 0.1 |
| Strength | 0.04 |
| Midlevel | 0.5 |

A GPU is needed for higher slice counts.

## Textures

Each texture can be changed individually. Different course layouts can be tested by replacing the course image.

### Gravel Texture Mix

Multiple repeating images are layered to reduce uniformity and add variation to the pavement texture. Adjust **Color** and **Color Magnitude** to change the brightness of the concrete.

**Location:** `Shade → Plane → Material.100 → Concrete`

### Parking Lines

The yellow parking lines add realism and provide a sense of scale. The robot should ignore these markings. Adjust the spray-paint transparency to change their appearance.

**Location:** `Shade → Plane → Material.100 → Parking Lot`

### Course Paint

White lines mark the boundaries within which the robot must remain. Adjust the spray-paint transparency to change their appearance.

**Location:** `Shade → Plane → Material.100 → Course Overlay`
