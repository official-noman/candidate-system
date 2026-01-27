"""
Candidate data generation script for recruitment system.
Generates Excel file with candidate information including work experience.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CandidateDataGenerator:
    """Generates candidate data for recruitment system import."""
    
    # Column definitions matching requirements
    REQUIRED_COLUMNS = ['Name', 'Email', 'Phone', 'Age', 'Experience (Years)']
    EXPERIENCE_COLUMNS = ['Company_1', 'Position_1', 'Company_2', 'Position_2']
    
    def __init__(self):
        self.data = self._initialize_data()
    
    def _initialize_data(self) -> dict:
        """Initialize candidate data structure."""
        return {
            # Basic Information
            'Name': [
                'John Doe', 'Michael Johnson', 'Ethan Roberts', 'Daniel Thompson',
                'James Anderson', 'David Clark', 'William Johnson', 'Robert Smith',
                'Michael Davis', 'Christopher Taylor', 'William Harris', 'Daniel Lee',
                'James Clark'
            ],
            'Email': [
                'johndoe@example.com', 'michael.johnson@ucla.edu', 
                'ethan.roberts@mit.edu', 'daniel.thompson@utexas.edu',
                'james.anderson@miami.edu', 'david.clark@gsu.edu',
                'william.johnson@uic.edu', 'robert.smith@harvard.edu',
                'michael.davis@uw.edu', 'christopher.taylor@stanford.edu',
                'william.harris@uchicago.edu', 'daniel.lee@usc.edu',
                'james.clark@nyu.edu'
            ],
            'Phone': [
                '917-555-1234', '323-555-6789', '617-555-4321', '832-555-2490',
                '305-555-1836', '404-555-1571', '312-555-3681', '617-555-0326',
                '206-555-7303', '415-555-1234', '312-555-4567', '323-555-7890',
                '212-555-6789'
            ],
            'Age': [25, 27, 25, 24, 23, 23, 25, 31, 32, 30, 29, 28, 27],
            'Experience (Years)': [3, 2, 2, 1, 2, 2, 4, 3, 6, 3, 3, 7, 1],
            
            # Work Experience - Primary Company
            'Company_1': [
                'TechWave Solutions', 'TechVision Solutions', 'Saffron',
                'PlayOn 24', 'Techdyno Bd Ltd', 'GlobalBangla Limited',
                'Ryven.CO', 'SA Tech & Consultancy', 'Zaman It',
                'Solution World Ltd', 'TechLab', 'weDevs Pte. Ltd.',
                'Fleek Bangladesh'
            ],
            'Position_1': [
                'Software Engineer', 'Software Engineer', 'Data Entry',
                'Software Engineer', 'Software Developer', 'IT Operation Officer',
                'Laravel Developer', 'Software Engineer', 'Laravel Developer',
                'Web Developer', 'Full Stack Engineer', 'Software Engineer',
                'Software Engineer'
            ],
            
            # Work Experience - Secondary Company (Optional)
            'Company_2': [
                'SparkTech Innovations', 'FutureTech Innovations', None, None,
                'Pioner Alpha', 'TechnoHack Edutech', 'Dreams enterprise',
                'App Maker BD', 'National Polymer', 'Matrix Business Development',
                'Nifty IT Solution', 'Alesha Tech Ltd', 'naztech Inc. Ltd'
            ],
            'Position_2': [
                'Intern', 'Jr. Software Engineer', None, None,
                'Intern Software Engineer', 'Data Analysis', 'Computer Operator',
                'Junior Software Engineer', 'Developer', 'Web Developer',
                'Full Stack Engineer', 'Web Application Developer',
                'Software Engineer Trainee'
            ]
        }
    
    def validate_data(self) -> bool:
        """Validate data integrity before export."""
        try:
            # Check all lists have same length
            lengths = [len(v) for v in self.data.values()]
            if len(set(lengths)) != 1:
                logger.error("Data columns have inconsistent lengths")
                return False
            
            # Validate required columns exist
            for col in self.REQUIRED_COLUMNS:
                if col not in self.data:
                    logger.error(f"Missing required column: {col}")
                    return False
            
            logger.info("Data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def generate_dataframe(self) -> pd.DataFrame:
        """Generate pandas DataFrame from candidate data."""
        if not self.validate_data():
            raise ValueError("Data validation failed")
        
        df = pd.DataFrame(self.data)
        logger.info(f"DataFrame created with {len(df)} candidates")
        return df
    
    def export_to_excel(
        self,
        filename: str = "candidates.xlsx",
        output_dir: str = "data"
    ) -> Path:
        """
        Export candidate data to Excel file.
        
        Args:
            filename: Output filename
            output_dir: Output directory path
            
        Returns:
            Path to the generated file
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate full file path
            file_path = output_path / filename
            
            # Generate and export DataFrame
            df = self.generate_dataframe()
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logger.info(f"Successfully exported data to '{file_path}'")
            logger.info(f"Total records: {len(df)}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise


def main():
    """Main execution function."""
    try:
        generator = CandidateDataGenerator()
        output_file = generator.export_to_excel()
        
        print(f"\n✓ Candidate data file created successfully!")
        print(f"  Location: {output_file.absolute()}")
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        raise


if __name__ == "__main__":
    main()


