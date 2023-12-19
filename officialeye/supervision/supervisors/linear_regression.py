from typing import Union

import click
import numpy as np

from officialeye.context.singleton import oe_context
from officialeye.supervision.result import SupervisionResult
from officialeye.supervision.supervisor import Supervisor


_IND_A = 0
_IND_B = 1
_IND_C = 2
_IND_D = 3


class LinearRegressionSupervisor(Supervisor):

    def run(self) -> Union[SupervisionResult, None]:
        match_count = self._kmr.get_total_match_count()

        best_result_error = np.inf
        best_result = None

        for anchor_match in self._kmr.get_matches():
            delta = anchor_match.get_original_template_point()
            delta_prime = anchor_match.get_target_point()

            matrix = np.zeros((match_count << 1, 4), dtype=np.float64)
            rhs = np.zeros(match_count << 1, dtype=np.float64)

            for i, match in enumerate(self._kmr.get_matches()):
                first_constraint_id = i << 1
                second_constraint_id = first_constraint_id + 1

                s = match.get_original_template_point()
                d = match.get_target_point()

                matrix[first_constraint_id][_IND_A] = s[0] - delta[0]
                matrix[first_constraint_id][_IND_B] = s[1] - delta[1]
                rhs[first_constraint_id] = d[0] - delta_prime[0]

                matrix[second_constraint_id][_IND_C] = s[0] - delta[0]
                matrix[second_constraint_id][_IND_D] = s[1] - delta[1]
                rhs[second_constraint_id] = d[1] - delta_prime[1]

            regression_matrix = matrix.T @ matrix
            regression_matrix = np.linalg.inv(regression_matrix)
            rhs_applied = matrix.T @ rhs
            x = regression_matrix @ rhs_applied

            transformation_matrix = np.array([
                [x[_IND_A], x[_IND_B]],
                [x[_IND_C], x[_IND_D]]
            ])

            _result = SupervisionResult(self.template_id, self._kmr, delta, delta_prime, transformation_matrix)
            _result_error = _result.get_mse()

            # error = matrix @ x - rhs
            # error_value = np.dot(error, error)

            if _result_error < best_result_error:
                if self.in_debug_mode() and not oe_context().quiet_mode:
                    click.secho(f"Improving error value from {best_result_error} to {_result_error}", fg="green")
                best_result_error = _result_error
                best_result = _result
            else:
                # using this anchor is not advantageous, we get large error
                if self.in_debug_mode() and not oe_context().quiet_mode:
                    click.secho(f"Error: {_result_error}", fg="yellow")

        return best_result