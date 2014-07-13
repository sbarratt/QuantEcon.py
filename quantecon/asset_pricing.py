"""
Filename: asset_pricing.py
Authors: David Evans, John Stachurski and Thomas J. Sargent

Computes asset prices in an endowment economy when the endowment obeys
geometric growth driven by a finite state Markov chain.  The transition matrix
of the Markov chain is P, and the set of states is s.  The discount
factor is beta, and gamma is the coefficient of relative risk aversion in the
household's utility function.
"""

import numpy as np
from numpy.linalg import solve

class AssetPrices:
    """
    A class to compute asset prices when the endowment follows a finite Markov
    chain.

    References
    ----------

        http://quant-econ.net/markov_asset.html

    Examples
    --------

        >>> n = 5
        >>> P = 0.0125 * np.ones((n, n))
        >>> P += np.diag(0.95 - 0.0125 * np.ones(5))
        >>> s = np.array([1.05, 1.025, 1.0, 0.975, 0.95])
        >>> gamma = 2.0
        >>> beta = 0.94
        >>> ap = AssetPrices(beta, P, s, gamma)
        >>> zeta = 1.0
        >>> v = ap.tree_price()
        >>> print "Lucas Tree Prices: ", v

        >>> v_consol = ap.consol_price(zeta)
        >>> print "Consol Bond Prices: ", v_consol

        >>> p_s = 150.0
        >>> w_bar, w_bars = ap.call_option(zeta, p_s, T = [10,20,30])


    """


    def __init__(self, beta, P, s, gamma):
        """
        Initializes an instance of AssetPrices

        Parameters
        ----------
        beta : float
            Discount factor

        P : array_like
            Transition matrix

        s : array_like
            Growth rate of consumption

        gamma : float
            Coefficient of risk aversion

        """
        self.beta, self.gamma = beta, gamma
        self.P, self.s = P, s
        self.n = self.P.shape[0]

    def tree_price(self):
        """
        Computes the function v such that the price of the lucas tree is
        v(lambda)C_t

        Returns
        -------
        v : np.ndarray
            Lucas tree prices
        """
        # == Simplify names == #
        P, s, gamma, beta = self.P, self.s, self.gamma, self.beta
        # == Compute v == #
        P_tilde = P * s**(1-gamma) #using broadcasting
        I = np.identity(self.n)
        O = np.ones(self.n)
        v = beta * solve(I - beta * P_tilde, P_tilde.dot(O))
        return v

    def consol_price(self, zeta):
        """
        Computes price of a consol bond with payoff zeta

        Parameters
        ----------
        zeta : float
            Coupon of the console

        Returns
        -------
        p_bar : np.ndarray
            Console bond prices

        """
        # == Simplify names == #
        P, s, gamma, beta = self.P, self.s, self.gamma, self.beta
        # == Compute price == #
        P_check = P * s**(-gamma)
        I = np.identity(self.n)
        O = np.ones(self.n)
        p_bar = beta * solve(I - beta * P_check, P_check.dot(zeta * O))
        return p_bar

    def call_option(self, zeta, p_s, T=[], epsilon=1e-8):
        """
        Computes price of a call option on a consol bond, both finite and
        infinite horizon

        Parameters
        ----------
        zeta : float
            Coupon of the console

        p_s : float
            Strike price

        T : list of integers
            Length of option in the finite horizon case

        epsilon : float, optional
            Tolerance for infinite horizon problem

        Returns
        -------
        w_bar : np.ndarray
            Infinite horizon call option prices

        w_bars : dict
            A dictionary of key-value pairs {t: vec}, where t is one of the
            dates in the list T and vec is the option prices at that date

        """
        # == Simplify names, initialize variables == #
        P, s, gamma, beta = self.P, self.s, self.gamma, self.beta
        P_check = P * s**(-gamma)
        # == Compute consol price == #
        v_bar = self.consol_price(zeta)
        # == Compute option price == #
        w_bar = np.zeros(self.n)
        error = epsilon + 1
        t = 0
        w_bars = {}
        while error > epsilon:
            if t in T:
                w_bars[t] = w_bar
            # == Maximize across columns == #
            to_stack = (beta*P_check.dot(w_bar), v_bar-p_s)
            w_bar_new = np.amax(np.vstack(to_stack), axis = 0 )
            # == Find maximal difference of each component == #
            error = np.amax(np.abs(w_bar-w_bar_new))
            # == Update == #
            w_bar = w_bar_new
            t += 1

        return w_bar, w_bars