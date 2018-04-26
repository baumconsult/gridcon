# -*- coding: utf-8 -*-
"""
Module to collect useful functions for economic calculations.
"""

def epc(capex, n, u, wacc, cost_decrease = 0, oc = 0):

    """
    function represents equivalent periodical costs of an economic activity

    parameters
    ----------
    capex: float
        capital expenditure for first investment per functional unit 
        (e.g. 1 kWh or 1 kW)
    n : int
        number of years investigated; might be an integer multiple of technical
        lifetime (u) in case of repeated investments; in case of a single
        investment, n must equal u
    u : int
        number of years that a single investment is used, i.e. the technical 
        lifetime of a single investment
    wacc : float
        weighted average cost of capital
    cost_decrease : float
        annual rate of cost decrease for repeated investments
        takes the value "0" if not set otherwise, that is in case of a single 
        investment or in case of no cost decrease for repeated investments
    oc : float
        fixed annual operational costs per functional unit (e.g. 1 kWh or 1 kW)
        takes the value "0" if not set otherwise

    """

    annuity_factor = (wacc*(1+wacc)**n)/((1+wacc)**n-1)
    
    # the annuity factor is the ratio of the equivalent annual costs of investment
    # (annuity) and the costs of investment in case of a single initial investment

    return (annuity_factor*capex*((1-((1-cost_decrease)/(1+wacc))**n) 
                                  /(1-((1-cost_decrease)/(1+wacc))**u)))+oc 
                                  
    # the value returned are the equivalent periodical (annual) costs of an
    # investment (annuity) plus the periodical fixed operational costs (oc);
    # the expression behind "capex" reflects the modification of the annuity
    # in case of repeated investments at fixed intervals u with decreasing costs;

   
