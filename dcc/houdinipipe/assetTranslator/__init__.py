"""

Python package to deal with translating assets from asset packages (like Megascan and Speed Tree) to Houdini.

Asset Accessor -> Asset Builder

Asset Accessor: Module that deals with getting the files from the asset package directory with custom implementations
for each asset package type.

    -  class AbstractAssetAccessor
    -  class MegascanAssetAccessor
    -  class SpeedTreeAssetAccessor

Asset Builder: Module that deals with building the asset in Houdini with custom implementations for each asset package.

    -  class AbstractAssetBuilder
        -  import geometry
        -  create variants
        -  import materials
        -  assign materials
        -  create variants
    -  class MegascanAssetBuilder
    -  class SpeedTreeAssetBuilder


helper functions:
 - build_mtlx_shader(name: str, textures: dict[str, system.Filepath], parent_node: hou.node) -> hou.node



 Specific implementation details:

 Megascan:
    - 3d Asset:
        - MAIN DIRECTORY (e.g. /3d_other_uhupbgxfa)
            - "previews" directory holding usually 1 image that is the pre-rendered preview render
            - "thumbs" directory of LQ texture previews. Pretty sure this can be ignored.
            - xxxx_4K_Albedo_LODX.jpg (Lod is optional here)
            - xxxx_4K_Displacement.exr
            - xxxx_LODX.fbx 3d model file with LOD[0-5]
    - 2d Texture Asset:
        - MAIN DIRECTORY (e.g. \rock_cliff_vl3ibcxlw)
            - "previews" directory holding usually 1 image that is the pre-rendered preview render
            - "thumbs" directory of LQ texture previews. Pretty sure this can be ignored.
            - xxxx_4K_Albedo.jpg (or whatever the texture is)
    - 3d Bundle Asset:
        - MAIN DIRECTORY (e.g. \debris_trash_sbfdv)
            - "previews" directory holding usually 1 image that is the pre-rendered preview render
            - "thumbs" directory of LQ texture previews. Pretty sure this can be ignored.
            - VarX (e.g. Var1, Var2, Var3, etc.) directory holding the 3d assets for each variant
                - VarX_LODX (e.g. Var1_LOD0, Var1_LOD1, Var1_LOD2, etc.) 3d assets for each LOD
            - "Textures"
                - "Atlas" meaning the textures go to a 3d model
                    - xxxx_4K_Albedo.jpg (or whatever the texture is)
                - "Billboard" meaning the textures go to a 2d plane - we can ignore this
"""