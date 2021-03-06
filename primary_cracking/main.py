import numpy as np
import matplotlib.pyplot as plt
import math
from io import BytesIO
import streamlit as st
import pandas as pd
from matplotlib.backends.backend_agg import RendererAgg
_lock = RendererAgg.lock
from summary import *

of_dict = {
    'A'  : {'Name' : 'Organo Facies A - Oil' , 'A' : float(2.13e13) , 'E' : float(206.4 * 1e3 * 0.000239006) , 's' : float(8.2 * 1000 * 0.000239006)},
    'B'  : {'Name' : 'Organo Facies B - Oil' , 'A' : float(8.14e13) , 'E' : float(215.2 * 1e3 * 0.000239006) , 's' : float(8.3 * 1000 * 0.000239006)},
    'C'  : {'Name' : 'Organo Facies C - Oil' , 'A' : float(2.44e14) , 'E' : float(221.4 * 1e3 * 0.000239006) , 's' : float(3.9 * 1000 * 0.000239006)},
    'DE' : {'Name' : 'Organo Facies DE - Oil', 'A' : float(4.97e14) , 'E' : float(228.2 * 1e3 * 0.000239006) , 's' : float(7.9 * 1000 * 0.000239006)},
    'F'  : {'Name' : 'Organo Facies F - Oil' , 'A' : float(1.23e17) , 'E' : float(259.1 * 1e3 * 0.000239006) , 's' : float(6.6 * 1000 * 0.000239006)}
    }

def Arrhenius(A, Ea, T, time): # time is in seconds, T is in Kelvin
    return math.exp(-time * A * math.exp(-Ea / (0.001987 * (T + 273))))


def computeEzRo(vitrinitetble ,T, dt):
    for i in range(vitrinitetble.shape[0]):
        vitrinitetble[i][1] *= Arrhenius(1.0e13 , vitrinitetble[i][0] , T , dt)
    Tr = (85.0 - np.sum(vitrinitetble , axis = 0)[1]) / 100.0
    return math.exp(-1.6 + 3.7 * Tr) / 100 , vitrinitetble


def primarycracking(kerogen, alpha):

    with _lock:
   
        labels = ["Temperature", "HI", "TR", "EasyRo", "TMax", "Thermal Stress", "Age"]
        np.set_printoptions(precision=2, suppress = True)
        temptable = np.linspace(30.,180.,16)
        vitrinitetble = np.array([[34.0 , 3.0],[36.0 , 3.0],[38.0 , 4.0],[40.0 , 4.0],[42.0 , 5.0],
                                [44.0 , 5.0],[46.0 , 6.0],[48.0 , 4.0],[50.0 , 4.0],[52.0 , 7.0],
                                [54.0 , 6.0],[56.0 , 6.0],[58.0 , 6.0],[60.0 , 5.0],[62.0 , 5.0],
                                [64.0 , 4.0],[66.0 , 3.0],[68.0 , 2.0],[70.0 , 2.0],[72.0 , 1.0]])
        T = 0
        T2 = 0
        age = 0
        sInMa = 60 * 60 * 24 *365 * 1e6
        result = []
        result_dict = {}
        maxT = 220
        dt = 1 / alpha #dt in Ma

        dts = sInMa * dt
        TMax = 0

        title = str(kerogen.name) + ' \n\n Kinetic scheme analysis'
        fig = plt.figure(title, figsize = (14,12))
        fig.suptitle(title, fontsize = 14 , fontweight = 'bold')
        
        ax = plt.subplot(231)
        xmin = min(kerogen.Ea) - 1
        xmax = max(kerogen.Ea) + 1
        ymin = 0
        ymax = max(kerogen.xi) + 50
        plt.axis([xmin, xmax, ymin, ymax])

        while T < maxT:
            for e in range(len(kerogen.Ea)):
                kerogen.xi[e] *= Arrhenius(kerogen.A , kerogen.Ea[e] , T , dts)

            # Compute HI
            HI = 0
            for c in kerogen.xi:
                HI += kerogen.dE * c

            for i in range(vitrinitetble.shape[0]):
                vitrinitetble[i][1] *= Arrhenius(1.0e13 , vitrinitetble[i][0] , T , dts)
            Tr = (85.0 - np.sum(vitrinitetble , axis = 0)[1]) / 100.0
            ezRo =  math.exp(-1.6 + 3.7 * Tr) / 100
            T2 = T - 15. * math.log(alpha / 2. , 10)

                # Initial heating : 5min @ 300C
            TR =  (1 - HI / kerogen.HI0)
            if TR < 1:
                RE_table = [kerogen.xi[e] for e in range(len(kerogen.Ea))]

                for e in range(len(kerogen.Ea)):
                    RE_table[e] *= Arrhenius(kerogen.A  , kerogen.Ea[e] , 300. , 300.)

                REYield = []
                for t in range(305,605,5):
                    for e in range(len(kerogen.Ea)):
                        RE_table[e] *= Arrhenius(kerogen.A  , kerogen.Ea[e] , t , 12)

                    REYielde = 0
                    for r in RE_table:
                        REYielde += kerogen.dE * r
                    REYield.append([t , REYielde])

                maxY = 0
                TMax1 = 0
                TMax2 = 0
                TMax3 = 0
                REYield = np.asarray(REYield)

                for k in range(1 , REYield.shape[0] - 1):
                    maxY = REYield[k - 1][1] - REYield[k][1]
                    if maxY > (REYield[k][1] - REYield[k+1][1]):
                        TMax1 = REYield[k - 1][0]
                        TMax2 = REYield[k + 0][0]
                        TMax3 = REYield[k + 1][0]
                        if k > 1 :
                            dY1 = REYield[k - 2][1] - REYield[k - 1][1]
                        else:
                            dY1 = 0
                        dY2 = REYield[k - 1][1] - REYield[k + 0][1]
                        dY3 = REYield[k + 0][1] - REYield[k + 1][1]
                        break

                matrix = [[TMax1 * TMax1 , TMax1 , 1],
                        [TMax2 * TMax2 , TMax2 , 1],
                        [TMax3 * TMax3 , TMax3 , 1]]
                matrix = np.asarray(matrix)

                try:
                    invmat = np.linalg.inv(matrix)
                    A = invmat[0][0] * dY1 + invmat[0][1] * dY2 + invmat[0][2] * dY3
                    B = invmat[1][0] * dY1 + invmat[1][1] * dY2 + invmat[1][2] * dY3
                    TMax = -B / (2 * A)
                    TMax = (TMax + 14) / 1.114 # Espitalie 1986
                except:
                    T += alpha * dt
                    continue

            result.append([T , HI , TR , ezRo , TMax , T2 , age])

            plt.xlabel('Activation Energy (kcal/mol)')
            plt.ylabel('Partial potential (mgHC/gC)')
            plt.title('Ea distribution vs. Maturity')
            if T in temptable:
                # label = str('% 0.2f' % float(100 * ezRo)) + '%Ro eq.'
                label = 'STS:' + str('% 0.0f' % float(T2)) + 'C'
                if kerogen.formalism == 'Pepper' :
                    ax.plot(kerogen.Ea, kerogen.xi, '-' , label = label)
                if kerogen.formalism == 'IFP' :
                    ax.bar(kerogen.Ea , kerogen.xi , label = label)
                ax.legend(fontsize = 8)

            T += alpha * dt
            age += dt
        ##### PLOT RESULTS #####
        result = np.asarray(result)
        result_df = pd.DataFrame(result, columns = labels)

        ax = plt.subplot(232)
        plt.xlabel('TMax (C)')
        plt.ylabel('Hydrogen Index (mgHC/gC)')
        plt.title('HI vs. TMax')
        xmin = 390
        xmax = 510
        ymin = 0
        ymax = 800
        plt.axis([xmin, xmax, ymin, ymax])
        a = result[:,1]
        b = result[:,4]

        ax.plot(b, a, 'o' , b , a)
        # ax.fill(x, y, zorder=10)
        ax.grid(True, zorder=5)

        ax = plt.subplot(233)
        plt.xlabel('Maturity (EasyRo, %VRo eq.)')
        plt.ylabel('Transformation ratio (/)')
        plt.title('TR vs. Maturity')
        xmin = 0.2
        xmax = 1.5
        ymin = 0
        ymax = 1.1
        plt.axis([xmin, xmax, ymin, ymax])
        a = 100 * result[:,3]
        b = result[:,2]
        ax.plot(a, b, 'o' , a , b)
        # ax.fill(x, y, zorder=10)
        ax.grid(True, zorder=5)

        ax = plt.subplot(234)
        plt.xlabel('Maturity (EasyRo, %VRo eq.)')
        plt.ylabel('TMax (C)')
        plt.title('TMax vs. Maturity')
        xmin = 0.4
        xmax = 1.5
        ymin = 390
        ymax = 510
        plt.axis([xmin, xmax, ymin, ymax])
        a = result[:,4]
        b = 100 * result[:,3]
        ax.plot(b, a, 'o' , b , a)
        # ax.fill(x, y, zorder=10)
        ax.grid(True, zorder=5)

        ax = plt.subplot(235)
        plt.xlabel('Maturity (EasyRo, %VRo eq.)')
        plt.ylabel('Temperature (C)')
        plt.title('Temperature vs. Maturity')
        xmin = 0.4
        xmax = 1.5
        ymin = 60.
        ymax = max(np.max(T2),np.max(T))
        plt.axis([xmin, xmax, ymin, ymax])
        a = 100 * result[:,3]
        b = result[:,0]
        c = result[:,5]
        ax.plot(a, b , label = 'Temperature')
        ax.plot(a, c , label = 'STS')
        # ax.fill(x, y, zorder=10)
        ax.grid(True, zorder=5)
        plt.legend()

        ax = plt.subplot(236)
        plt.xlabel('Time (Ma)')
        plt.ylabel('Temperature (C)')
        plt.title('Heating rate ' + str(alpha) + 'C/Ma')
        xmin = 0.
        xmax = T / alpha
        ymin = 0.
        ymax = max(np.max(T2),np.max(T))
        plt.axis([xmin, xmax, ymin, ymax])
        a = result[:,6]
        b = result[:,0]
        c = result[:,5]
        ax.plot(a, b , label = 'Temperature')
        ax.plot(a, c , label = 'STS')
        # ax.fill(x, y, zorder=10)
        ax.grid(True, zorder=5)
        plt.legend()

    return result_df, fig




class KerogenPepper:
    def __init__(self, name, A , Emean, s , HI0):
        self.name = name
        self.formalism = 'Pepper'
        self.A = A
        self.HI0 = None
        self.xi = None
        self.s = s
        self.Emean = Emean
        factor = 5.
        Ea = np.linspace(Emean - factor * s , Emean + factor * s , 250, retstep = True)
        self.Ea = Ea[0]
        self.dE = Ea[1]
        self.update_xi(HI0)

    def update_xi(self, HI0):
        self.HI0 = HI0
        self.xi = list(map(lambda e : HI0 *  ((1 / (self.s * math.sqrt(2 * math.pi))) * math.exp(-(math.pow(e - self.Emean , 2)) / (2 * math.pow(self.s , 2)))) , self.Ea))


# def compute(HI, OF, alpha):
    
#     of_select = of_dict[OF]
#     kero  = KerogenPepper(of_select['Name'] ,  of_select['A'] ,  of_select['E'] ,  of_select['s'] , float(HI))

#     primarycracking(kero , float(alpha))

#     with open("a.png", "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read())

#     return [{"type": "image", "data": {"alt": "could not compute", "src": "data:image/png;base64, " + encoded_string.decode('ascii')}}]

def compute_cracking(OF, HI, alpha):
    '''
    Compute primary cracking for a given kerogen and heating rate

    Parameters:
    - OF (str) : Organo facies label ['A', 'B', 'C', 'DE', 'F']
    - HI0 (int) : initial Hydrogen Index (mgHC/gC)
    - alpha (float ): heating rate(C/Ma)

    Returns:
    - Pandas Dataframe with the simulated values
    - Matplotlib figure object
    '''
    plt.close()
    of_select = of_dict[OF]
    kero  = KerogenPepper(of_select['Name'] ,  of_select['A'] ,  of_select['E'] ,  of_select['s'] , float(HI))
    with _lock:
        result_df, fig = primarycracking(kero , float(alpha))

    return result_df, fig


def st_ui():
    st.set_page_config(layout = "wide")

    

    st.title("Primary Cracking simulation")
    OF = st.sidebar.selectbox('OrganoFacies selection', ('A', 'B', 'C', 'DE', 'F'))
    HI = st.sidebar.slider("Initial Hydrogen Index", 100, 900, 600)
    alpha = st.sidebar.slider("Heating rate", 0.1, 10., 2.)

    with st.expander("Summary"):
        st.markdown(get_summary(OF, HI, alpha))

    result_df, fig = compute_cracking(OF, HI, alpha)

    with _lock:
        st.header("Primary cracking dashboard")
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', transparent = True)
        st.image(buf, use_column_width=False, caption='Primary Cracking dashboard')
    
    st.header("Simulated data")
    st.dataframe(result_df)



if __name__ == '__main__':
    st_ui()