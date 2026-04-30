# Run MEE analysis from a script.
from mee2024.api import find_stars, compute_distortion, fit_data                                                         
                                                                                                                       
# find_stars('configs/station1-sample-find-stars-calibration.toml')                                                        
# compute_distortion('configs/station1-sample-compute-distortion-zenith.toml')                                             
find_stars('configs/station1-sample-find-stars-eclipse.toml')                                                            
compute_distortion('configs/station1-sample-compute-distortion-eclipse.toml')                                            
fit_data('configs/station1-sample-fit-data.toml')  
