"""

USD LAYER STRUCTURE

- Each layer has its own hip file

shot.usd
    - LAYOUT
        - add assets
        - default camera
        - default lighting
    - ANIMATION
        - animation
    - FX ( optional )
        - fx
    - LIGHTING and RENDERING
        - lighting and camera prim settings

Workflow:
    - Create USD assets
    - Add it to the layout via the asset loader

"""