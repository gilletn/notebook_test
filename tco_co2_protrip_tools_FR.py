import requests
import pandas as pd
import plotly.graph_objects as go
import plotly as plt
from plotly.subplots import make_subplots
import numpy as np
import datetime
import getpass
import os


class WS:
   def __init__(self):
      self.proxies = dict()
      self.headers = {
          "Content-Type": "application/json",
          "Accept": "application/json"}
      mobicloudUrl = 'https://mobicloud.ifpen.com'
      url = mobicloudUrl+'/api/authenticate'
      login = getpass.getpass("Mobicloud login (%s):"%mobicloudUrl)
      password = getpass.getpass("Mobicloud password :")
      data = {"password": password, "rememberMe": True, "username": login}
      r = requests.post(url, json=data, headers=self.headers, proxies=self.proxies)
      del login, password, data
      TOKEN = r.json().get('id_token',None)
      if TOKEN is None:
         print('Error during login, try again ...')
      else:
         print(' => success !')
         self.headers['Authorization'] = "Bearer "+TOKEN
      self.urlbase = mobicloudUrl+"/tco/service/"

# limit the choice of powertrains to compare
pwtChoice = ['VE', 'VFH_plugin_P2', 'VMH_D', 'VTH_D']
# pwtChoice = ['VE +', 'VFH_plugin_P2', 'VMH_D', 'VTH_D']
# pwtChoice = ['CM_VE', 'CM_VFH_plugin_P2', 'CM_VMH_D', 'CM_VTH_D']

# correspondence for plotting
labelsDict = {
    "VE +": "Electrique BEV",
    "VE": "Electrique BEV",
    "VFH_plugin_P2": "Hybride réchargeable PHEV",
    "VFH_plugin_P2_CS": "hybride réchargeable (mode dégradé)",
    "VFH_P2": "hybride full Essence",
    "VMH_D": "Hybride mild Diesel MHEV",
    "VMH_G": "hybride mild Essence",
    "VTH_D": "Start & Stop Diesel",
    "VTH_G": "thermique Essence",
}


def createPlots(fleetResults,inputDataFrame):
    # Create traces
    cols = plt.colors.DEFAULT_PLOTLY_COLORS
    # x = datetime.datetime.now()
    # year = x.year
    year = datetime.datetime.now().year
    for iFleet, subFleetResults in enumerate(fleetResults):
        if inputDataFrame['Nb vehicules'].iloc[iFleet]:
            vehicleAndPwtChoice = [subFleetResults['cars'][0].split('_', 1)[0] + '_' + i for i in pwtChoice]

            fig = make_subplots(rows=2, cols=2, start_cell="bottom-left",
                                subplot_titles=('CO2 Puits à la roue', 'CO2 equivalent ACV', "Coût d'usage",
                                                'TCO'))
            for iPwt, vehPwt in enumerate(vehicleAndPwtChoice):
                fig.add_trace(go.Scatter(x=subFleetResults['TCOY']['years'],
                                         y=subFleetResults['TCOY'][vehPwt],
                                         mode='lines+markers',
                                         name=labelsDict[pwtChoice[iPwt]], showlegend=False, legendgroup=vehPwt,
                                         line=dict(width=2, color=cols[iPwt]),
                                         ),
                              row=2, col=2)
                fig.add_trace(go.Scatter(x=subFleetResults['TCOY']['years'],
                                         y=subFleetResults['EnergyCostFctYear'][vehPwt],
                                         mode='lines+markers',
                                         name=labelsDict[pwtChoice[iPwt]], showlegend=False, legendgroup=vehPwt,
                                         line=dict(width=2, color=cols[iPwt]),
                                         ),
                              row=2, col=1)
                fig.add_trace(go.Scatter(x=subFleetResults['TCOY']['years'],
                                         y=subFleetResults['CO2WtWFctYear'][vehPwt],
                                         mode='lines+markers',
                                         name=labelsDict[pwtChoice[iPwt]], showlegend=False, legendgroup=vehPwt,
                                         line=dict(width=2, color=cols[iPwt]),
                                         ),
                              row=1, col=1)
                fig.add_trace(go.Scatter(x=subFleetResults['TCOY']['years'],
                                         y=subFleetResults['CO2LCAFctYear'][vehPwt],
                                         mode='lines+markers',
                                         name=labelsDict[pwtChoice[iPwt]], showlegend=True, legendgroup=vehPwt,
                                         line=dict(width=2, color=cols[iPwt]),
                                         ),
                              row=1, col=2)

            fig.update_layout(
                xaxis=dict(
                    tickmode='linear',
                    # tick0=0.5,
                    dtick=1
                ),
                title_text='Usage ' + str(iFleet +1)+ ': ' + inputDataFrame['Label Usage'][iFleet]
            )
            # Update xaxis properties
            fig.update_xaxes(title_text="Year", row=1, col=1)
            fig.update_xaxes(title_text="Year", row=1, col=2)
            fig.update_xaxes(title_text="Year", row=2, col=1)
            fig.update_xaxes(title_text="Year", row=2, col=2)

            # Update yaxis properties
            fig.update_yaxes(title_text="CO2 eq. in Mt", row=1, col=1)
            fig.update_yaxes(title_text="CO2 eq. in Mt", row=1, col=2)
            fig.update_yaxes(title_text="Cost in €", row=2, col=1)
            fig.update_yaxes(title_text="Cost in €", row=2, col=2)

            fig.show()
            # return fig

# convert output data to dataframe for displaying
def createResultDf(fleetResults, inputDataFrame):
    fleetDict = {}
    fleetDfList = []
    bestTcoList = []

    temp = pwtChoice[:]
    temp.append('meilleur TCO')
    # fleetDfList.append(pd.DataFrame(fleetDict[iFleet])*inputDataFrame['Nb vehicules'][iFleet])
    fleetCostDf = pd.DataFrame(columns = ['Coût total de possession [€]', 'Coût total énergie [€]', 'CO2 equivalent total [Mt CO2eq]', 'CO2 equivalent énergie [Mt CO2eq]'], index = temp).fillna(0)
    # print(fleetCostDf)
    for iFleet, subFleetResults in enumerate(fleetResults):
        # vehicleAndPwtChoice = [subFleetResults['cars'][0].split('_', 1)[0] + '_' + i for i in pwtChoice]
        #
        # resultsDict = {}
        # tempList =[]

        tcoDict = {}
        enrDict = {}
        tCO2eqDict = {}
        tCO2enrDict = {}
        elecRangeDict = {}
        nbRechargeDict = {}
        timeRecharge7kWDict = {}
        timeRecharge43kWDict = {}

        # for iPwt, vehPwt in enumerate(vehicleAndPwtChoice):
        for iPwt, pwt in enumerate(pwtChoice):
            vehPwt = subFleetResults['cars'][0].split('_', 1)[0] + '_' + pwt
            # tempList.append(subFleetResults['TCO'][subFleetResults['cars'].index(vehPwt)])
            tcoDict[pwt] = subFleetResults['TCO'][subFleetResults['cars'].index(vehPwt)]
            enrDict[pwt] = subFleetResults['costUsage'][subFleetResults['cars'].index(vehPwt)]
            tCO2eqDict[pwt] = subFleetResults['tCO2eq'][subFleetResults['cars'].index(vehPwt)]
            tCO2enrDict[pwt] = subFleetResults['tCO2eqUsage'][subFleetResults['cars'].index(vehPwt)]
            elecRangeDict[pwt] = subFleetResults['rangeElecKm'][subFleetResults['cars'].index(vehPwt)]
            nbRechargeDict[pwt] = subFleetResults['nbRecharge'][subFleetResults['cars'].index(vehPwt)]
            timeRecharge7kWDict[pwt] = ('{}h {} min'.format(int(subFleetResults['timeRecharge7kW'][subFleetResults['cars'].index(vehPwt)][0]), int(subFleetResults['timeRecharge7kW'][subFleetResults['cars'].index(vehPwt)][1])))
            timeRecharge43kWDict[pwt] = ('{}h {} min'.format(int(subFleetResults['timeRecharge43kW'][subFleetResults['cars'].index(vehPwt)][0]), int(subFleetResults['timeRecharge43kW'][subFleetResults['cars'].index(vehPwt)][1])))

            tempBestPwt = min(tcoDict, key=tcoDict.get)
        bestTcoList.append(tempBestPwt)
        tcoDict['meilleur TCO'] = tcoDict[tempBestPwt]
        enrDict['meilleur TCO'] = enrDict[tempBestPwt]
        tCO2eqDict['meilleur TCO'] = tCO2eqDict[tempBestPwt]
        tCO2enrDict['meilleur TCO'] = tCO2enrDict[tempBestPwt]

        fleetDict[iFleet] = {'Coût total de possession [€]': tcoDict,
                             'Coût total énergie [€]': enrDict,
                             'CO2 equivalent total [Mt CO2eq]': tCO2eqDict,
                             'CO2 equivalent énergie [Mt CO2eq]': tCO2enrDict,
                             'Autonomie électrique [km]': elecRangeDict,
                             'Nb de recharges nécessaires (ZEV)': nbRechargeDict,
                             'Durée recharge à 7kW': timeRecharge7kWDict,
                             'Durée recharge à 43kW': timeRecharge43kWDict}
        # fleetDfList.append(pd.DataFrame(fleetDict[iFleet]).fillna(value='')*inputDataFrame['Nb vehicules'][iFleet])
        temp_df = pd.DataFrame(fleetDict[iFleet])
        temp_df.loc[:,'Coût total de possession [€]':'CO2 equivalent énergie [Mt CO2eq]'] = temp_df.loc[:,'Coût total de possession [€]':'CO2 equivalent énergie [Mt CO2eq]']*inputDataFrame['Nb vehicules'][iFleet]
        # fleetDfList.append(pd.DataFrame(fleetDict[iFleet]).fillna(value='')*inputDataFrame['Nb vehicules'][iFleet])
        fleetDfList.append(temp_df.fillna(value=''))
        fleetCostDf += pd.DataFrame(fleetDict[iFleet])*inputDataFrame['Nb vehicules'][iFleet]

    bestTcoDf = pd.DataFrame((zip(inputDataFrame['Label Usage'],bestTcoList)), columns=['Label Usage','meilleur TCO'])
    output = {'meilleur TCO': bestTcoDf, 'Tableau résultat per usage': fleetDfList, 'Coût de possession flotte': fleetCostDf}
    return output




