# gridcon
rural energy systems including electrified high-power agricultural machinery and renewable energy generation

The programme gridcon_storage_171222d.py is the last version of the programme developed in the project GridCon (www.gridcon-project.de) for calculating the cost-optimal combination of a local grid connection, an energy storage and PV curtailment of a rural energy system comprising a base demand, a high-power electrified agricultural machine (1.2 MW) and PV installations. It is based on the example programme storage_investment and uses oemof v0.1.

The tool economics_BAUM.py is based on the tool economics.py using oemof v0.1. It allows calculating the equivalent periodical costs of a series of investments with initial costs exponentially decreasing in time. This reflects for instance the case of lithium-ion battery systems which have a much shorter lifetime than electric grids, such needing replacement within longer financial periods. At the same time the initial costs of lithium-ion batteries are dramatically decreasing. The mathematics behind the formulae in economics_BAUM.py is comprehensively explained in German in the document "economics_BAUM_171128_kommentiert3.pdf

The background and results obtained with the grid_storage_171222d.py within the project GridCon and the first months of the follow-up project GridCon2 as well as results obtained previously within the project SESAM (www.sesam-project.de) have been presented at the IRES 2018 in Düsseldorf. The slides of the presentation at the IRES 2018 and the final publication in Energy Procedia are included.

The full report on the work done in GridCon is only available in German.
