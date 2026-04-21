import logging
import numpy as np

logger = logging.getLogger(__name__)

class FractalService:
    """
    Service responsible for calculating the fractal dimension of segmentation masks.
    Uses the Minkowski-Bouligand (box-counting) algorithm to estimate geometric complexity.
    """

    @staticmethod
    def calculate_dimension(binary_mask: np.ndarray) -> float:
        """
        Calculates the box-counting fractal dimension of a binary mask.
        
        The algorithm applies a logarithmic regression over the number of boxes
        required to cover the active pixels at different grid scales.
        
        Formula: D = lim(L->0) [log(N(L)) / log(1/L)]
        Where N(L) is the number of boxes of size L containing at least one positive pixel.

        Args:
            binary_mask (np.ndarray): A 2D numpy array where the region of interest is > 0.

        Returns:
            float: The estimated fractal dimension (typically between 1.0 and 2.0).
        """
        if binary_mask is None or binary_mask.size == 0:
            
            logger.warning("Empty mask provided for fractal calculation.")
            
            return 0.0

        #  Normalize input to a strict 2D boolean array
        if len(binary_mask.shape) > 2:
            
            binary_mask = binary_mask[:, :, 0]
            
        boolean_mask = (binary_mask > 0)
        
        # GSaeve  clauses for trivial masks (empty or completely full)
        if not np.any(boolean_mask):
            
            return 0.0
        
        if np.all(boolean_mask):
            
            return 2.0

        #  Pad the image to the next power of 2 for efficient reshaping
        max_dimension = max(boolean_mask.shape)
        power = int(np.ceil(np.log2(max_dimension)))
        padded_size = 2 ** power
        
        padded_mask = np.zeros((padded_size, padded_size), dtype=bool)
        padded_mask[:boolean_mask.shape[0], :boolean_mask.shape[1]] = boolean_mask

        # Iterative Box Counting
        # Generate descending box sizes: 2^p, 2^(p-1), ..., 1
        box_sizes = 2 ** np.arange(power, -1, -1)
        
        box_counts = []

        for size in box_sizes:
            
            if size == 1:
                # If box size is 1x1, the count is simply the total number of True pixels
                box_counts.append(np.sum(padded_mask))
                continue
            
            # Calculate the grid layout for the current box size
            grid_shape = (padded_size // size, size, padded_size // size, size)
            
            # Reshape into a 4D array where dimensions 1 and 3 represent the contents of each box
            reshaped_grid = padded_mask.reshape(grid_shape)
            
            # Check if any pixel within each box is True, then count the active boxes
            active_boxes = reshaped_grid.any(axis=(1, 3))
            box_counts.append(np.sum(active_boxes))

        # 4. Log-Log Linear Regression
        # Convert lists to numpy arrays and filter out invalid zero counts to avoid log(0) errors
        sizes_array = np.array(box_sizes, dtype=np.float64)
        counts_array = np.array(box_counts, dtype=np.float64)
        
        valid_indices = counts_array > 0
        
        if np.sum(valid_indices) < 2:
            
            return 0.0
            
        valid_sizes = sizes_array[valid_indices]
        valid_counts = counts_array[valid_indices]
        
        # log(N(L)) = -D * log(L) + C  ->  Slope is -D
        log_sizes = np.log(valid_sizes)
        log_counts = np.log(valid_counts)
        
        # Use numpy.polyfit for a degree 1 polynomial (linear regression)
        coefficients = np.polyfit(log_sizes, log_counts, 1)
        # Minkowski-Bouligand dimension is the negative of the slope
        slope = coefficients[0]
        
        fractal_dimension = -slope
        
        return float(round(fractal_dimension, 4))
    

    @staticmethod
    def evaluate_severity(fractal_dimension: float, area_cm2: float) -> str:
        """
        Evaluates the severity level of the corrosion patch based on its 
        geometric complexity (fractal dimension) and physical extent.

        Args:
            fractal_dimension (float): The calculated Minkowski-Bouligand dimension.
            area_cm2 (float): The physical area of the corrosion in square centimeters.

        Returns:
            str: Severity classification label ('Low', 'Medium', 'High', 'Critical').
        """
        if fractal_dimension == 0.0 or area_cm2 == 0.0:
            return "None"
            
        # Pitting corrosion (high tortuosity) is inherently more dangerous
        # than uniform surface corrosion, hence higher fractal dimensions escalate the severity.
        if fractal_dimension > 1.80 or area_cm2 > 100.0:
            
            return "Critical"
        
        elif fractal_dimension > 1.50 and area_cm2 > 50.0:
            
            return "High"
        
        elif fractal_dimension > 1.30 or area_cm2 > 20.0:
            
            return "Medium"
        
        else:
            
            return "Low"