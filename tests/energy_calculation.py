import os
import ihelper as i

def calculate_energy_directory(devices = ['agx-xavier-00', 'LoudJetson0', 'xavier-nx-00'],
                               measurement_code = 'Representative',
                               checkModes = False,
                               checkFreqs = True,
                               ):
    """
    Calculates the energy consumption based on the power and performance files.

    """

    for device in devices:
            
        # Specify the directory
        directory = f'/home/louduser/LoudVA/measurements/archive/{measurement_code}/{device}/measurements'

        if checkFreqs:

            # Create the energy directory if it does not exist
            if not os.path.exists(f'{directory}/energy/freqs'):
                os.makedirs(f'{directory}/energy/freqs')

            # Get the list of files and directories
            contents = os.listdir(f'{directory}/performance/freqs')

            # Print each item
            for performance_file in contents:
                if performance_file.endswith('.csv'):
                    freq = performance_file.split('_')[-1].split('.')[0]
                    power_file = f'{directory}/power/freqs/power_measurement_stats_freq_{freq}.csv'
                    energy_file = f'{directory}/energy/freqs/energy_calculated_freq_{freq}.csv'
                    performance_file = f'{directory}/performance/freqs/{performance_file}'
                    i.calculate_energy(power_file, performance_file, energy_file)

        if checkModes:

            # Create the energy directory if it does not exist
            if not os.path.exists(f'{directory}/energy/modes'):
                os.makedirs(f'{directory}/energy/modes')
                
            # Get the list of files and directories
            contents = os.listdir(f'{directory}/performance/modes')

            # Print each item
            for performance_file in contents:
                if performance_file.endswith('.csv'):
                    mode = performance_file.split('_')[-1].split('.')[0]
                    power_file = f'{directory}/power/modes/power_measurement_stats_mode_{mode}.csv'
                    energy_file = f'{directory}/energy/modes/energy_calculated_mode_{mode}.csv'
                    performance_file = f'{directory}/performance/modes/{performance_file}'
                    i.calculate_energy(power_file, performance_file, energy_file)


calculate_energy_directory()