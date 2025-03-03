import pandas as pd
import os

class FormComparator:

    def __init__(self, f1, f2, output_dir = ".", output_xlsx="comparison_results.xlsx"):
        """
        Initializes the XLSComparator with a name and an optional XLSX filename.
        
        :param output_xlsx: Filename for exporting comparison results.
        """

        if output_dir != ".":
            os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
            self._output_path = os.path.join(output_dir, output_xlsx)
        else:
            self._output_path = output_xlsx
        self._comparisons = {}  # Dictionary to store comparison results

        self._f1 = f1
        self._f2 = f2

        self._generic_df = f1.getSurvey()#pd.DataFrame()
        self._settings_df = pd.DataFrame()
        with pd.ExcelWriter(self._output_path, engine="xlsxwriter") as writer:
            self._generic_df.to_excel(writer, sheet_name="overview", index=False)
            self._settings_df.to_excel(writer, sheet_name="settings", index=False)

    def getOutputRelativePath(self):

        return self._output_path
        
    # Instance Methods
    def addComparison(self, key, result, value1, value2):
        """
        Adds a new comparison result to the dictionary.
        
        :param key: The type of comparison (e.g., "ID", "Version").
        :param result: The comparison result (e.g., "identical", "different").
        :param value1: First value being compared.
        :param value2: Second value being compared.
        """
        self._comparisons[key] = {
            "Finding": result,
            "f1": value1,
            "f2": value2
        }

    def export2XLSX(self):
        """Exports the comparison results to an Excel file with conditional formatting."""
        if not self._comparisons:
            print("No comparisons to export.")
            return

        # Convert dictionary to DataFrame
        df = pd.DataFrame.from_dict(self._comparisons, orient="index").reset_index()
        df.columns = ["Comparison Type", "Finding", "f1", "f2"]

        # Ensure output directory exists
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, self._output_xlsx)

        # Write to Excel with formatting
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="settings", index=False)

            # Access workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets["settings"]

            # Define formatting styles
            green_format = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})  # Green
            red_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})  # Red

            # Apply formatting based on "Finding" column
            for row in range(1, len(df) + 1):  # Skip header row
                finding = df.iloc[row - 1, 1]  # "Finding" column
                cell_format = green_format if finding == "identical" else red_format
                worksheet.set_row(row, None, cell_format)

        print(f"Comparison results exported to {output_path}")