##################################################################################
# IMPORTS
##################################################################################

# outputlib

from oemof import outputlib

# default logger of oemof

from oemof.tools import logger
from oemof.tools import helpers
from oemof.tools import economics_BAUM

    # economics is a tool to calculate the equivalent periodical cost (epc) of 
    # an investment; 
    # it has been modified by B.A.U.M. Consult GmbH within the frame of the 
    # GridCon project (www.gridcon-project.de) and the modified version 
    # has been called "economics_BAUM";
    # it allows now calculting epc of a series of investments with a defined
    # cost-decrease rate;
    # it also allows taking into account fixed periodical costs such as staff 
    # cost and offset fixed periodical income;

from pyomo import environ
import oemof.solph as solph

# import oemof base classes to create energy system objects

import logging
import os
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# import load and generation data from csv-file and define timesteps

def optimise_storage_size(filename="GridCon1_Profile.csv", 
                          solver='cbc', debug=True, number_timesteps= (96*366),
                          tee_switch=True):
    
    # the file "GridCon1_Profile" contains the normalised profile for the 
    # agricultural base load profile L2, a synthetic electrified agricultural 
    # machine load profile, and the PV generation profile ES0;
    # number_timesteps: one timestep has a duration of 15 minutes, 
    # hence, 96 is the number of timesteps per day;
    # 366 is the number of days in a leap year, chosen here because 
    # standard load profils of 2016 are used;
    # the total number of timesteps is therefore 96*366 = 35136;

# initialise energysystem, date, time increment
    
    logging.info('Initialise the Energysystem')
    
    date_time_index = pd.date_range('1/1/2016', periods=number_timesteps, 
                                                                freq='15min')
    energysystem = solph.EnergySystem(timeindex=date_time_index)

    time_step = 0.25 
    
    # a 15 minutes time step equals 0.25 hours;

# read data file

    full_filename = os.path.join(os.path.dirname(__file__), filename)
    data = pd.read_csv(full_filename, sep=",")

##################################################################################
# DEFINITION OF TO-BE-OPTIMISED STRUCTURES
##################################################################################

# definition of the investigated (financial) period for which the optimisation
# is performed; 
# needs to be the same for all objects whose costs are taken into account;

    n = 50

    # financial period in years for which equivalent periodical costs of 
    # different options are compared;

# definition of the specific investment costs of those objects whose size is
# optimised; here, the electric grid connection and the electrical storage;
# the electric grid connection considered here comprises the local mv-lv trans-
# former plus the respective share of the entire up-stream grid;
# as a consequence of oemof allowing to handle only positive flow values, the
# grid connection needs to be modelled twice: a "collecting half" for the electric 
# power flow from the local lv-grid to a far point in the up-stream grid (it
# collects electricty generated in areas where generation exceeds the demand at
# a given moment), and a "supplying half" for the inverse flow from that far 
# point to the local grid (it supplies areas where the demand exceeds the 
# generation at a given moment);
    
    invest_grid = 500
    
    # assumed specific investment costs of the electric transformer linking the 
    # low voltage and the medium voltage grid including respective share of 
    # up-stream grid costs in €/kW;
    # the value is taken from a real price (about 200000 €) paid by an investor
    # for grid connection of about 400 kW active power provision capacity (at the
    # low-voltage side of the transformer) set up for a new large load in a 
    # rural area; this amount contains essentially upstream grid costs;
    # source: oral communication from a private investor;
    
    invest_el_lv_1_storage = 300
    
    # assumed specific investment costs of electric energy storage system in €/kWh
    # figure reflects roughly specific investment costs of lithium-ion batteries;
    # source: Sterner/Stadler, Energiespeicher, p. 600 (indicates 170 - 600 €/kWh)

# definition of parameters entering in the calculation of the equivalent 
# periodical costs (epc) of the electric transformer and the up-stream grid;

    wacc = 0.05

    # assumed weighted average cost of capital; 
    
    u_grid = 50

    # assumed technical lifetime of electric transformer and up-stream grid;

    cost_decrease_grid = 0

    # indicates the relative annual decrease of investment costs;
    # allows calculating the cost of a second or any further investment
    # a certain number of years after the first one;
    # here, only one investment in the electric transformer and up-stream grid
    # is considered to be made here within the financial period;
    # hence, there is no cost decrease and the variable takes the value zero;

    oc_rate_grid = 0.02

    # percentage of initial investment costs assumed for calculation of 
    # specific annual fixed operational costs of electric transformer and 
    # up-stream grid;

    oc_grid = oc_rate_grid * invest_grid

    # specific annual fixed operational costs of electric transformer and 
    # up-stream grid in €/kW of active power provision capacity;

# calculation of specific equivalent periodical costs (epc) i.e. the annual costs 
# equivalent to the investment costs (annuitiy) plus the fixed operational costs 
# of the electric transformer and the up-stream grid per kW of active power
# provision capacity;      
                  
    sepc_grid = economics_BAUM.epc(invest_grid, n, u_grid, wacc, 
                                      cost_decrease_grid, oc_grid)

    # specific equivalent periodical costs of transformer and of up-stream grid
    # in €/kW;
                                                                                                                                                                       
# definition of parameters entering in the calculation of the equivalent
# periodical costs of the electric energy storage system;

    u_el_lv_1_storage = 5

    # assumed technical lifetime of electric energy storage system

    cost_decrease_el_lv_1_storage = 0.1

    # assumed annual cost decrease rate for newly installed electric energy
    # storage systems; reflects roughly learning curve for lithium-ion battery
    # storage systems in 2010-2016;

    oc_rate_el_lv_1_storage = 0.02

    # percentage of specific initial investment costs assumed for calculation of 
    # specific annual fixed operational costs of electric storage system;

    oc_el_lv_1_storage = oc_rate_el_lv_1_storage * invest_el_lv_1_storage

    # specific annual fixed operational costs of electric storage system in €/kWh;

# calculation of specific equivalent periodical costs (sepc in €/kWh/year) 
# i.e. the specific annual costs equivalent to the investment costs (annuitiy) 
# plus the fixed operational costs of the electric energy storage system;      
                  
    sepc_el_lv_1_storage = economics_BAUM.epc(invest_el_lv_1_storage, n, 
                                       u_el_lv_1_storage, wacc,
                                       cost_decrease_el_lv_1_storage, 
                                       oc_el_lv_1_storage)
    
    kS_el = sepc_el_lv_1_storage
    
    # equivalent specific annual costs of electric energy storage system in €/kWh;
    # refers to nominal storage capacity;

# calculation of income from provision of primary balancing power by electric
# energy storage system; income is substracted from equivalent periodical costs;

    prl_on = 1

    # if primary balancing power is planned to be provided by the energy storage,
    # set value "1", otherwise "0";

    prl_weeks = 13

    # number of entire weeks for which primary balancing power is planned to be 
    # provided
    
    prl_income = 2.4 * prl_on * prl_weeks

    # corresponds to specific annual income per kWh of nominal electric energy 
    # storage capacity, i.e. expressed in €/kWh, generated by provision 
    # of primary balancing power in Germany at a remuneration of 3000 €/week by 
    # an energy storage with a charge/ discharge rate of at least 1 MW per MWh 
    # of storage capacity operated between 10% and 90% of its nominal capacity; 

    sepc_el_lv_1_storage = sepc_el_lv_1_storage - prl_income
    
    kS_el_netto = sepc_el_lv_1_storage

    # net specific equivalent periodical costs of electric energy storage system 
    # taking into account income generated from provision of primary balancing 
    # power;
       
##################################################################################
# CREATION OF OEMOF STRUCTURE
##################################################################################

    logging.info('Constructing GridCon energy system structure')
    
##################################################################################
# CREATION OF BUSES REPRESENTING ENERGY DISTRIBUTION
##################################################################################
    
    b_el_mv = solph.Bus(label="b_el_mv")

    # creates medium voltage electric grid

    b_el_lv = solph.Bus(label="b_el_lv")

    # creates low voltage electric grid
    
##################################################################################
# CREATION OF SOURCE OBJECTS
##################################################################################
    
    solph.Source(label='mv_source', outputs={b_el_mv: solph.Flow()})    

    # represents aggregated electric generators at a far point in the up-stream
    # grid; here, no limit is considered for this source;
    
    solph.Source(label='el_lv_7_pv', outputs={b_el_lv: 
        solph.Flow(actual_value=data['pv'], nominal_value = 1, fixed=True)}) 

    # represents aggregated pv power plants in investigated area which are looked
    # at as a single source of energy;
    # "outputs={b_el_lv: ...}" defines that this source is connected to the 
    # low voltage grid;
    # "solph.Flow ..." defines properties of this connection: actual_value get 
    # the pv generation data for all time intervals from csv-file;
    # "nominal_value = 1" signifies that pv generation data do not need further 
    # processing, they are already absolute figures in kW;
    # "fixed=True" signifies that these data are not modified by the solver;
    
    solph.Source(label='el_lv_6_grid_excess', outputs={b_el_lv: solph.Flow(
            variable_costs = 100000000)})   

    # dummy producer of electric energy connected to low voltage grid; 
    # introduced to ensure energy balance in case no other solution is found;
    # extremely high variable costs ensure that source is normally not used;
    
##################################################################################
# CREATION OF SINK OBJECTS
##################################################################################    

    solph.Sink(label='el_mv_sink', inputs={b_el_mv: solph.Flow()})

    # represents aggregated consumers at a far point in the up-stream grid;
    # here, it is assumed that no limit exists for this sink;
    
    solph.Sink(label='el_lv_2_base_load', inputs={b_el_lv: 
        solph.Flow(actual_value=data['demand_el'], nominal_value= 1, fixed=True)})

    # represents base load in low voltage (lv) electric grid;
    # "inputs={b_el_lv: ...}" defines that this sink is connected to the
    # low-voltage electric grid;
    # "solph.Flow ..." defines properties of this connection: actual_value 
    # gets the base load data for all time intervals from csv-file;
    # "nominal_value = 1" signifies that base load data do not need further
    # processing, they are already absolute figures in kW;
    # "fixed=True" signifies that these data are not modified by the solver;

    solph.Sink(label='el_lv_3_machine_load', inputs={b_el_lv: 
        solph.Flow(actual_value=data['machine_load'], 
                   nominal_value= 1, fixed=True)})    

    # represents electrified agricultural machine connected to lv-grid;
    # "inputs={b_el_lv: ...}" defines that this sink is connected to the
    # low voltage electric grid;
    # "solph.Flow ..." defines properties of this connection: actual_value 
    # gets the electrified agricultural machine load data for all time 
    # intervals from csv-file;
    # "nominal_value = 1" signifies that base load data do not need further 
    # processing, they are already absolute figures in kW;
    # "fixed=True" signifies that these data are not modified by the solver;

    cost_electricity_losses = 6.5E-2

    # (unit) cost that a farmer or equivalent investor in grid extension and/or 
    # electric energy storage pays for 1 kWh of electric energy which is lost;
    # the value of 0.065 €/kWh corresponds to assumed average cost of electricity 
    # in a future energy system with predominant generation from PV and wind
    # power plants;
            
    curtailment = solph.Sink(label='el_lv_4_excess_sink', inputs={b_el_lv: 
        solph.Flow(variable_costs = cost_electricity_losses)})

    # represents curtailment of electric energy from PV plants, i.e. that part
    # of possible PV electricity generation which is actually not generated by
    # tuning the PV power electronics such that the output is reduced below the
    # instantaneous maximum power;
    # "inputs={b_el_lv: ...}" defines that this "sink" is connected to the 
    # low voltage electric grid;
    # "solph.Flow ..." defines properties of this connection: variable_costs
    # are set at costs of electricity which is lost;
          
##################################################################################
# CREATION OF TRANSFORMER OBJECTS
##################################################################################     

# as a consequence of oemof allowing to handle only positive flow values,the local
# mv-lv transformer needs to be modelled by two different objects, one for the
# electric power flow from the local lv-grid to a far point in the up-stream grid, 
# one for the inverse flow from that far point to the local grid;
# each (!) of the two objects represents, for the respective power flow direction,
# not only the local mv-lv transformer, but the whole grid infrastructure between 
# a virtuel power supplier/ sink at a far point in the up-stream grid and the 
# local lv-grid, including all grid lines and voltage transformation steps;

    grid_loss_rate = 0.0685
    
    # rate of losses within the entire up-stream grid including the local
    # transformer;
    # the value of 6.85% reflects average grid losses in Germany from January 
    # to September 2017;
    # source: https://www.destatis.de/DE/ZahlenFakten/Wirtschaftsbereiche/
    # Energie/Erzeugung/Tabellen/BilanzElektrizitaetsversorgung.html 
    # [last retrieved on 16 November 2017];
    
    grid_eff = 1 - grid_loss_rate
    
    # effective efficiency of power transmission in the up-stream grid;
     
    transformer_mv_to_lv = solph.LinearTransformer(label="transformer_mv_to_lv", 
            inputs={b_el_mv: solph.Flow(variable_costs = 
                        (grid_loss_rate * cost_electricity_losses))}, 
            outputs={b_el_lv: solph.Flow(investment=solph.Investment
                                                    (ep_costs=0.5 * sepc_grid))}, 
            conversion_factors={b_el_lv: grid_eff})              

    # represents the "supplying half" of the whole up-stream grid including the
    # "mv-to-lv electric transformer", i.e. that "half" of the
    # physical local transformer linking the low and medium voltage grid 
    # "in the direction mv -> lv";
    # "input" designates source bus of electricity, here: medium-voltage grid; 
    # variable costs are cost of electricity lost within one time interval in
    # the up-stream grid and transformer; they are a fraction of the electricity
    # generated at a far point in the up-stream grid times the cost of 
    # electricity which gets lost;
    # "output" designates destination bus of electricity, here: low-voltage grid;
    # fixed grid costs (epc), i.e. costs of "supplying half" of local transformer
    # and up-stream grid are attributed to output, because it is the lv-side 
    # whose size has to be determined in the optimisation process;
    # the conversion factor defines the ratio between the output flow, here the
    # electricity flowing from the local transformer into the low-voltage grid, 
    # and the input flow, here the electricity injected into the up-stream grid 
    # at a far point;
                
    transformer_lv_to_mv = solph.LinearTransformer(label="transformer_lv_to_mv",
                            inputs={b_el_lv: solph.Flow(investment = 
                                solph.Investment(ep_costs = 0.5 * sepc_grid))}, 
                            outputs={b_el_mv: solph.Flow(variable_costs = 
                        (cost_electricity_losses*grid_loss_rate/grid_eff))}, 
                        conversion_factors = {b_el_mv: grid_eff})
             
    # represents the "collecting half" of the whole up-stream grid including the
    # local "lv-to-mv electric transformer", i.e. that "half" of the
    # physical local transformer linking the low and medium voltage grid 
    # "in the direction lv -> mv";
    # "input" designates source bus of electricity, here: low-voltage grid;
    # fixed grid costs (epc), i.e. the epc of the "collecting half" of local 
    # transformer and up-stream grid are attributed to input, because it is 
    # the lv-side whose size needs to match the rest of the modelled system;
    # "output" designates the destination bus of electricity, 
    # here: medium-voltage grid;
    # variable costs are cost of electricity lost within one time interval in
    # the transformer and up-stream grid; they are a fraction of the electricity
    # generated in the modelled system and fed into the up-stream grid times the 
    # cost of electricity which gets lost;
    # the conversion factor defines the ratio between the output flow, here the 
    # electric power flow consumed at a far point in the up-stream grid, and the
    # input flow, here the electricity flowing from the low-voltage grid into the 
    # transformer; 

##################################################################################
# CREATION OF STORAGE OBJECTS
##################################################################################       
   
    icf = 0.95

    ocf = 0.95

    # charging (icf) and discharging efficiency of the electric energy storage;
    # the values reflect the efficiency of a lithium-ion battery with typical 
    # input, respectively output electronic converters;

    el_storage_conversion_factor = icf * ocf

    # approximate term for effective efficiency of electric energy storage system
    # used for calculating the costs of electricity lost in the electric energy
    # storage system; for this purpose, and only for this purpose, self-discharge 
    # losses are neglected;    

    solph.Storage(label='el_lv_1_storage',
            inputs={b_el_lv: solph.Flow(variable_costs = cost_electricity_losses
            *(1-el_storage_conversion_factor))}, outputs={b_el_lv: solph.Flow()},
            capacity_min = 0.1, capacity_max = 0.9,
            nominal_input_capacity_ratio = 1,
            nominal_output_capacity_ratio = 1,
            inflow_conversion_factor = icf, outflow_conversion_factor = ocf, 
            capacity_loss = 0.0000025,
            investment=solph.Investment(ep_costs = sepc_el_lv_1_storage))  

    # represents electric energy storage (input and output are electricity)
    # "input" designates source of electricity charging the storage, here the 
    # low voltage electricity grid, "output" the same for sink of electricity 
    # discharged from the storage;
    # "capacity_min" and "capacity_max" designate, respectively, the minimum and
    # maximum state of charge of the storage, related to its maximum energy 
    # content;
    # values are typical for operation of lithium-ion batteries in practical 
    # applications;
    # "inflow_conversion_factor" and "outflow_conversion_factor" designate, 
    # respectively, the efficiency of the charging and discharging process;
    # "capacity_loss" reflects the self-discharge of the storage per timestep as 
    # a fraction of the energy contained in the storage in the preceding timestep;
    # the value 0.0000025 (0.00025%) corresponds to the self-discharge within 
    # 15 minutes, respectively 0.024% per day; that is in the midth of the 
    # typical range of 0,008-0,041% per day for lithium-ion batteries
    # source: Sterner/Stadler, Energiespeicher, p. 600;
     
##################################################################################
# OPTIMISATION OF THE ENERGY SYSTEM
##################################################################################

    logging.info('Optimise the energysystem')

# initialise the operational model

    om = solph.OperationalModel(energysystem)
        
# adding constraint

    my_block = environ.Block()

    def connect_invest_rule(m):        
        expr = (om.InvestmentFlow.invest[b_el_lv, transformer_lv_to_mv] ==
                om.InvestmentFlow.invest[transformer_mv_to_lv, b_el_lv])
        return expr
    
    my_block.invest_connect_constr = environ.Constraint(
            rule=connect_invest_rule)
    om.add_component('ConnectInvest', my_block)

    # defines that upper limit for energy flow from electric transformer to 
    # medium voltage grid equals upper limit for energy flow from transformer 
    # to low voltage;
    # the fact that the maximum is addressed instead of the value in a specific 
    # timestep is reflected by the string ".invest" in the name of the objects;
        
# if debug is true an lp-file will be written

    if debug:
        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), 'GridCon.lp')
        logging.info('Store lp-file in {0}.'.format(filename))
        om.write(filename, io_options={'symbolic_solver_labels': True})

# if tee_switch is true solver messages will be displayed

    logging.info('Solve the optimisation problem')
    om.solve(solver=solver, solve_kwargs={'tee': tee_switch})
    
# Visualisation of results

    el_lv_1_storage = energysystem.groups['el_lv_1_storage']
    
    print(' ') 
    print('CAPACITY OF GRID CONNECTION')
    print('####################################################')
    print(' ')
    print('Grid collection capacity:  ', energysystem.results
                              [ b_el_lv][transformer_lv_to_mv].invest, 'kW')
    print('Grid supply capacity:      ', energysystem.results
                              [ transformer_mv_to_lv][b_el_lv].invest, 'kW')
    print(' kN:                       ', sepc_grid, '€/kW')
    print(' ')
    print('CAPACITY OF ELECTRIC ENERGY STORAGE')
    print('####################################################')
    print(' ')
    print('Storage capacity:          ', energysystem.results
                            [el_lv_1_storage][el_lv_1_storage].invest, 'kWh')
    print(' kS:                       ', kS_el,  '€/kWh')
    print(' PRL income:               ', prl_income,   '€/kWh')
    print(' kS_netto:                 ', kS_el_netto,  '€/kWh')
    print(' ')
    print('COST BREAKDOWN')
    print('####################################################')
    print(' ')
    print('Fixed grid costs:          ', om.InvestmentFlow.investment_costs(),'€')
    print('Fixed storage costs:       ', om.InvestmentStorage.investment_costs(), 
                                                                             '€')
    print('Total fixed costs:         ', om.InvestmentFlow.investment_costs() +
                                    om.InvestmentStorage.investment_costs(), '€')
    print(' ')
    print('Costs of grid losses:      ', sum(energysystem.results[b_el_mv]
                               [transformer_mv_to_lv]) * cost_electricity_losses 
                            * grid_loss_rate * time_step 
            + sum(energysystem.results[b_el_lv][transformer_lv_to_mv])
                * cost_electricity_losses * grid_loss_rate * time_step,'€')
    print('Costs of storage losses:   ', sum(energysystem.results[b_el_lv]
                            [el_lv_1_storage]) * cost_electricity_losses * 
                            (1-el_storage_conversion_factor) * time_step, '€')
    print('Costs of curtailment:      ', sum(energysystem.results[b_el_lv]
                    [curtailment]) * cost_electricity_losses * time_step, '€')
    print('Total variable costs:      ',om.Flow.variable_costs(), '€')
    print(' ') 
    print('Total annual costs         ', om.InvestmentFlow.investment_costs()
                    + om.InvestmentStorage.investment_costs()
                    + om.Flow.variable_costs(), '€')
    print('--------------------------------------------------')
    print('Objective function:        ', energysystem.results.objective, '€')
    print('Accordance:                ', (om.InvestmentFlow.investment_costs()
                    + om.InvestmentStorage.investment_costs() 
                    + om.Flow.variable_costs())
                        / energysystem.results.objective*100, '%')
    print(' ')
    print('####################################################')
    print(' ')
    print(' ')
    return energysystem

##################################################################################
# GENERATION OF CSV-FILE 
##################################################################################

def create_csv(energysystem):

    results = outputlib.ResultsDataFrame(energy_system=energysystem)    
    results.bus_balance_to_csv(bus_labels=['b_el_lv'],
                               output_path='results_as_csv_LV_Net')
   
def run_GridCon_example(**kwargs):
    logger.define_logging()
    esys = optimise_storage_size(**kwargs)

    if plt is not None:
        create_csv(esys)
   
if __name__ == "__main__":
    run_GridCon_example()
