#!/bin/env python3

import scipy.integrate as integrate
import matplotlib.pyplot as plt
import numpy as np

class ChannelModel:
    # Voltage as a function of time
    V = lambda t: 0

    #state probabilities
    ProbabilityOpen = 0
    ProbabilityClosed = 1
    ProbabilityInactive = 0

    # Intracellular and extracellular concentrations of potassium.
    K_out = 4
    K_in  = 130

    # valency of ions (1 in the case of K^+)
    z = 1

    #Parameters. Maximal conductance is P[8].
    P = [0] * 9

    #transition rates
    k1 = 0
    k2 = 0
    k3 = 0
    k4 = 0

    #Constructor to set Parameters values
    def __init__(self, params, voltage_function = lambda x: 0):
        self.P = params
        self.V = voltage_function

    def setTransitionRates(self, V):
        self.k1 = self.P[0] * np.exp(self.P[1]*V)
        self.k2 = self.P[2] * np.exp(-self.P[3]*V)
        self.k3 = self.P[4] * np.exp(self.P[5]*V)
        self.k4 = self.P[6] * np.exp(-self.P[7] * V)

    def getProbabilityICState(self):
        return 1 - self.ProbabilityOpen - self.ProbabilityClosed - self.ProbabilityInactive


    def getDPrClosedDt(self):
        return -(self.k1 + self.k3)*self.ProbabilityClosed + self.k2*self.ProbabilityOpen + self.k4*self.getProbabilityICState()

    def getDPrOpenDt(self):
        return -(self.k2 + self.k3)*self.ProbabilityOpen + self.k1*self.ProbabilityClosed + self.k4 * self.ProbabilityInactive

    def getDPrInactiveDt(self):
        return -(self.k2 + self.k4) * self.ProbabilityInactive + self.k3*self.ProbabilityOpen + self.k1*self.getProbabilityICState()

    #Calculate the current through the membrane in nano amps
    def getCurrent(self, V):
        # G is maximal conductance
        G = self.P[-1]
        # E is the Nernst potential for potassium ions across the membrane
        # Gas constant R, temperature T, Faradays constat F
        R = 8.3145
        T = 25
        F = 96485

        #Nernst potential
        E = R*T/(self.z*F) * np.log(self.K_out/self.K_in)
        return G * self.ProbabilityOpen*(V - E)

    def getStates(self, t):
        voltage = self.V(t)
        self.setTransitionRates(voltage)
        return np.ndarray(shape=(3,), buffer=np.array([self.ProbabilityClosed, self.ProbabilityOpen, self.ProbabilityInactive]))

    def setStates(self,X):
        self.ProbabilityClosed = X[0]
        self.ProbabilityOpen = X[1]
        self.ProbabilityInactive = X[2]

    def getDerivatives(self, t, X):
        self.setStates(X)
        X = self.getStates(t)
        return [self.getDPrClosedDt(), self.getDPrOpenDt(), self.getDPrInactiveDt()]

    def getTransitionRates(self, t=0):
        self.setTransitionRates(t)
        return [self.k1, self.k2, self.k3, self.k4]

    def calculateCurrent(self, probC, probO, probI, t=0):
        self.ProbabilityOpen = probO
        self.ProbabilityClosed = probC
        self.ProbabilityInactive = probI
        return self.getCurrent(self.V(t))

def main():
    t = 1000
    params = [2.26E-04, 0.0699, 3.45E-05, 0.05462, 0.0873, 8.92E-03, 5.150E-3, 0.03158, 0.1524]
    model = ChannelModel(params, lambda t: -80)
    print(model.getTransitionRates())
    initial_conditions = model.getStates(0)
    print(model.getStates(0))
    solution = integrate.solve_ivp(model.getDerivatives, [0,t], model.getStates(0))
    y = solution.y
    IVec = [model.calculateCurrent(y[0,t], y[1,t], y[2,t]) for t in range(0,len(solution.t))]
    plt.plot(solution.t, solution.y[1])
    plt.plot(solution.t, IVec)
    plt.show()

if __name__ == '__main__':
    main()