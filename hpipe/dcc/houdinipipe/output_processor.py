import hou
from husd.outputprocessor import OutputProcessor


class ReviewOutputProcessor(OutputProcessor):
    @staticmethod
    def name():
        return "merp"
    @staticmethod
    def displayName():
        return "Display Merp"

    def processSavePath(self, asset_path, referencing_layer_path, asset_is_layer):
        # Make the asset path absolute
        asset_path = hou.text.abspath(asset_path)

        # This processor asks the user to manually rewrite every file path.
        # This is just an example, don't do this! It would be annoying!
        return hou.ui.readInput(
            message="Rewrite this output file path if you want",
            initial_contents=asset_path,
            buttons=("OK",),
        )

    def processReferencePath(self, asset_path, referencing_layer_path, asset_is_layer):
        # Make file path pointers relative to the source file's location
        return 'merp'


# Must have: module-level function to return the processor class
def usdOutputProcessor():
    return ReviewOutputProcessor