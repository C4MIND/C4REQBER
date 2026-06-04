"""Tests for Game Theory — Nash Equilibrium module."""

from __future__ import annotations

import pytest

from src.game_theory.nash import NashEquilibrium, find_pure_nash


class TestNashEquilibrium:
    def test_create_equilibrium(self):
        ne = NashEquilibrium(
            strategies=[0, 1],
            payoffs=[3.0, 5.0],
            is_pure=True,
        )
        assert ne.strategies == [0, 1]
        assert ne.payoffs == [3.0, 5.0]
        assert ne.is_pure is True


class TestFindPureNash:
    def test_empty_matrix(self):
        result = find_pure_nash([])
        assert result == []

    def test_prisoners_dilemma(self):
        # Standard PD: (C,C)=(3,3), (C,D)=(0,5), (D,C)=(5,0), (D,D)=(1,1)
        payoff = [
            [[3, 0], [5, 1]],  # Player 1
            [[3, 5], [0, 1]],  # Player 2
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 1
        assert result[0].strategies == [1, 1]  # (Defect, Defect)
        assert result[0].payoffs == [1.0, 1.0]
        assert result[0].is_pure is True

    def test_battle_of_sexes(self):
        # (Opera,Opera)=(3,2), (Opera,Football)=(0,0), (Football,Opera)=(0,0), (Football,Football)=(2,3)
        payoff = [
            [[3, 0], [0, 2]],
            [[2, 0], [0, 3]],
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 2
        strategies_set = {tuple(ne.strategies) for ne in result}
        assert (0, 0) in strategies_set
        assert (1, 1) in strategies_set

    def test_stag_hunt(self):
        # (Stag,Stag)=(4,4), (Stag,Hare)=(0,3), (Hare,Stag)=(3,0), (Hare,Hare)=(3,3)
        payoff = [
            [[4, 0], [3, 3]],
            [[4, 3], [0, 3]],
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 2
        strategies_set = {tuple(ne.strategies) for ne in result}
        assert (0, 0) in strategies_set
        assert (1, 1) in strategies_set

    def test_matching_pennies_no_pure_nash(self):
        payoff = [
            [[1, -1], [-1, 1]],
            [[-1, 1], [1, -1]],
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 0

    def test_dominant_strategy(self):
        # Player 1 has a strictly dominant strategy [0]
        payoff = [
            [[5, 3], [4, 2]],
            [[1, 0], [2, -1]],
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 1
        assert result[0].strategies == [0, 0]

    def test_payoffs_are_correct(self):
        payoff = [
            [[10, 5], [0, 0]],
            [[10, 0], [5, 0]],
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 1
        assert result[0].payoffs == [10.0, 10.0]

    def test_no_deviation_detection(self):
        # Modify PD to make (C,C) not Nash: P1 gets 10 by defecting against C
        payoff = [
            [[3, 0], [10, 1]],
            [[3, 5], [0, 1]],
        ]
        result = find_pure_nash(payoff)
        strategies_set = {tuple(ne.strategies) for ne in result}
        assert (0, 0) not in strategies_set

    def test_multiple_equilibria_payoff_dominance(self):
        # (0,0) payoff-dominates (1,1) but both are Nash
        payoff = [
            [[10, 0], [0, 1]],
            [[10, 0], [0, 1]],
        ]
        result = find_pure_nash(payoff)
        assert len(result) == 2
