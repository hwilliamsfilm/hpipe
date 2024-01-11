"""
This is the asset loader for Houdini. It is called by the asset_manager.py
"""
import hou
from apps.pipeDisplay import output_gui
from core import data_manager
from hutil.Qt import QtCore
from assets import usdAsset
from core.hutils import logger
from importlib import reload
reload(output_gui)
reload(usdAsset)
reload(data_manager)

log = logger.setup_logger()
log.debug("asset_loader.py loaded")


def browse_button(kwargs) -> bool:
    """
    Browse button callback
    :param kwargs:
    :return:
    """
    node = hou.pwd()
    window = output_gui.OutputViewer(show_side_bar=False, size=(1000, 500), start_type='Assets', font_scale=.8, icon_size=200)
    window.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    if window.exec_():
        solution = window.return_value

    if not solution:
        log.warning("Could not receive value from output_gui")
        return False

    asset_name = solution['filepath']
    asset_manager = data_manager.AssetDataManager()
    usd_asset: usdAsset.UsdAsset = asset_manager.get_asset(asset_name)
    filepath = usd_asset.get_filepath().system_path()
    node.parm('_assetpath').set(filepath)
    node.parm('_assetname').set(usd_asset.asset_name)
    return True

