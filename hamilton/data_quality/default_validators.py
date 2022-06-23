import abc
import numbers
from typing import Any, Type, List, Optional, Tuple, Union, NewType

import numpy
import numpy as np

from hamilton.data_quality import base
import pandas as pd
from datetime import datetime


Comparable = NewType("Comparable", Union[float, datetime])


class BaseDefaultValidator(base.DataValidator, abc.ABC):
    """Base class for a default validator.
    These are all validators that utilize a single argument to be passed to the decorator check_output.
    check_output can thus delegate to multiple of these. This is an internal abstraction to allow for easy
    creation of validators.
    """

    def __init__(self, importance: str):
        super(BaseDefaultValidator, self).__init__(importance)

    @classmethod
    @abc.abstractmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        pass

    @abc.abstractmethod
    def description(self) -> str:
        pass

    @abc.abstractmethod
    def validate(self, data: Any) -> base.ValidationResult:
        pass

    @classmethod
    @abc.abstractmethod
    def arg(cls) -> str:
        """Yields a string that represents this validator's argument.
        @check_output() will be passed a series of kwargs, each one of which will correspond to
        one of these default validators. Note that we have the limitation of allowing just a single
        argument.

        :return: The argument that this needs.
        """
        pass


class DataInRangeValidatorPandas(BaseDefaultValidator):
    def __init__(self, range: Tuple[Comparable, Comparable], importance: str):
        """Data validator that tells if data is in a range. This applies to primitives (ints, floats) and datetimes.

        :param range: Inclusive range of parameters
        """
        super(DataInRangeValidatorPandas, self).__init__(importance=importance)
        self.range = range
        self.lower, self.upper = self.range


    @classmethod
    def arg(cls) -> str:
        return 'range'

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return issubclass(datatype, Union[pd.Series, pd.DataFrame])

    @classmethod
    def name(cls) -> str:
        return 'data_in_range_validator'

    def description(self) -> str:
        if self.upper is None:
            return f'Validates that the datapoint >= {self.lower}'
        elif self.lower is None:
            return f'Validates that the datapoint <= {self.upper}'
        return f'Validates that the datapoint falls within the range ({self.lower}, {self.upper})'

    def validate(self, data: Union[pd.DataFrame, pd.Series]) -> base.ValidationResult:
        if isinstance(data, pd.DataFrame):
            return self._validate_dataframe(data)
        elif isinstance(data, pd.Series):
            return self._validate_series(data)
        raise NotImplementedError(f"{type(data)=} not supported.")

    def _validate_series(self, data: pd.Series) -> base.ValidationResult:
        # TODO: toggle bound inclusivity?
        if self.lower is None:
            between = data.le(self.upper)
        elif self.upper is None:
            between = data.ge(self.lower)
        else:
            between = data.between(self.lower, self.upper, inclusive="both")
        counts = between.value_counts().to_dict()
        empirical_min = data.min()
        empirical_max = data.max()
        in_range = counts.get(True, 0)
        out_range = counts.get(False, 0)
        passes = out_range == 0
        message = f'Series contains {in_range} values in range ({self.lower},{self.upper}), and {out_range} outside. Data observed in range [{empirical_min}, {empirical_max}].'

        return base.ValidationResult(
            passes=passes,
            message=message,
            diagnostics={
                'range': self.range,
                'in_range': in_range,
                'out_range': out_range,
                'data_size': len(data)
            }
        )

    def _validate_dataframe(self, data: pd.DataFrame) -> base.ValidationResult:
        # TODO: toggle bound inclusivity?
        total = data.count()

        if self.lower is not None:
            lower = data >= self.lower
        else:
            lower = total
        if self.upper is not None:
            upper = data <= self.upper
        else:
            upper = total

        between = upper & lower


        ranges = pd.DataFrame(
                [data.min(), data.max(), lower.sum(), upper.sum(), between.sum(), total],
                index=["min", "max", "above_lower_bound", "below_upper_bound", "in_range", "count"]
            ).to_dict()

        out_range = {k:v for k,v in ranges.items() if v["in_range"] < v["count"]}


        passes = len(out_range) == 0

        message = f'DataFrame contains {len(ranges) - len(out_range)} columns in range ({self.lower},{self.upper}), and {len(out_range)} outside'

        return base.ValidationResult(
            passes=passes,
            message=message,
            diagnostics=out_range
        )



class DataInRangeValidatorPrimitives(BaseDefaultValidator):
    def __init__(self, range: Tuple[Comparable, Comparable], importance: str):
        """Data validator that tells if data is in a range. This applies to primitives (ints, floats).

        :param range: Inclusive range of parameters
        """
        super(DataInRangeValidatorPrimitives, self).__init__(importance=importance)
        self.range = range

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return issubclass(datatype, numbers.Real)

    def description(self) -> str:
        return f'Validates that the datapoint falls within the range ({self.range[0]}, {self.range[1]})'

    def validate(self, data: numbers.Real) -> base.ValidationResult:
        min_, max_ = self.range
        passes = min_ <= data <= max_
        message = f'Data point {data} falls within acceptable range: ({min_}, {max_})' if passes else \
            f'Data point {data} does not fall within acceptable range: ({min_}, {max_})'
        return base.ValidationResult(
            passes=passes,
            message=message,
            diagnostics={
                'range': self.range,
                'value': data
            }
        )

    @classmethod
    def arg(cls) -> str:
        return 'range'

    @classmethod
    def name(cls) -> str:
        return 'data_in_range_validator'


class MaxFractionNansValidatorPandasSeries(BaseDefaultValidator):
    def __init__(self, max_fraction_nan: float, importance: str):
        super(MaxFractionNansValidatorPandasSeries, self).__init__(importance=importance)
        MaxFractionNansValidatorPandasSeries._validate_max_fraction_nan(max_fraction_nan)
        self.max_fraction_nan = max_fraction_nan

    @staticmethod
    def _to_percent(fraction: float):
        return '{0:.2%}'.format(fraction)

    @classmethod
    def name(cls) -> str:
        return 'max_fraction_nan_validator'

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return issubclass(datatype, pd.Series)

    def description(self) -> str:
        return f'Validates that no more than {MaxFractionNansValidatorPandasSeries._to_percent(self.max_fraction_nan)} of the data is Nan.'

    def validate(self, data: pd.Series) -> base.ValidationResult:
        total_length = len(data)
        total_na = data.isna().sum()
        fraction_na = total_na / total_length
        passes = fraction_na <= self.max_fraction_nan
        return base.ValidationResult(
            passes=passes,
            message=f'Out of {total_length} items in the series, {total_na} of them are Nan, '
                    f'representing: {MaxFractionNansValidatorPandasSeries._to_percent(fraction_na)}. '
                    f'Max allowable Nans is: {MaxFractionNansValidatorPandasSeries._to_percent(self.max_fraction_nan)},'
                    f' so this {"passes" if passes else "does not pass"}.',
            diagnostics={
                'total_nan': total_na,
                'total_length': total_length,
                'fraction_na': fraction_na,
                'max_fraction_na': self.max_fraction_nan
            }
        )

    @classmethod
    def arg(cls) -> str:
        return 'max_fraction_nan'

    @staticmethod
    def _validate_max_fraction_nan(max_fraction_nan: float):
        if not (0 <= max_fraction_nan <= 1):
            raise ValueError(f'Maximum fraction allowed to be nan must be in range [0,1]')


class NansAllowedValidatorPandas(MaxFractionNansValidatorPandasSeries):
    def __init__(self, allow_nans: bool, importance: str):
        if allow_nans:
            raise ValueError(f'Only allowed to block Nans with this validator.'
                             f'Otherwise leave blank or specify the percentage of Nans using {MaxFractionNansValidatorPandasSeries.name()}')
        super(NansAllowedValidatorPandas, self).__init__(max_fraction_nan=0 if not allow_nans else 1.0, importance=importance)

    @classmethod
    def name(cls) -> str:
        return 'nans_allowed_validator'

    @classmethod
    def arg(cls) -> str:
        return 'allow_nans'


class DataTypeValidatorPandas(BaseDefaultValidator):

    def __init__(self, datatype: Type[Type], importance: str):
        super(DataTypeValidatorPandas, self).__init__(importance=importance)
        DataTypeValidatorPandas.datatype = datatype
        self.datatype = datatype

    @classmethod
    def name(cls) -> str:
        return 'dtype_validator'

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return issubclass(datatype, pd.Series)

    def description(self) -> str:
        return f'Validates that the datatype of the pandas series is a subclass of: {self.datatype}'

    def validate(self, data: pd.Series) -> base.ValidationResult:
        dtype = data.dtype
        passes = np.issubdtype(dtype, self.datatype)
        return base.ValidationResult(
            passes=passes,
            message=f"Requires subclass of datatype: {self.datatype}. Got datatype: {dtype}. This {'is' if passes else 'is not'} a valid subclass.",
            diagnostics={
                'required_dtype': self.datatype,
                'actual_dtype': dtype
            }
        )

    @classmethod
    def arg(cls) -> str:
        return 'datatype'


class PandasMaxStandardDevValidator(BaseDefaultValidator):
    def __init__(self, max_standard_dev: float, importance: str):
        super(PandasMaxStandardDevValidator, self).__init__(importance)
        self.max_standard_dev = max_standard_dev

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return issubclass(datatype, pd.Series)

    def description(self) -> str:
        return f'Validates that the standard deviation of a pandas series is no greater than : {self.max_standard_dev}'

    def validate(self, data: pd.Series) -> base.ValidationResult:
        standard_dev = data.std()
        passes = standard_dev <= self.max_standard_dev
        return base.ValidationResult(
            passes=passes,
            message=f'Max allowable standard dev is: {self.max_standard_dev}. '
                    f'Dataset stddev is : {standard_dev}. '
                    f"This {'passes' if passes else 'does not pass'}.",
            diagnostics={
                'standard_dev': standard_dev,
                'max_standard_dev': self.max_standard_dev
            }
        )

    @classmethod
    def arg(cls) -> str:
        return 'max_standard_dev'

    @classmethod
    def name(cls) -> str:
        return 'max_standard_dev_validator'


class PandasMeanInRangeValidator(BaseDefaultValidator):

    def __init__(self, mean_in_range: Tuple[float, float], importance: str):
        super(PandasMeanInRangeValidator, self).__init__(importance)
        self.mean_in_range = mean_in_range

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return issubclass(datatype, pd.Series)

    def description(self) -> str:
        return f'Validates that a pandas series has mean in range [{self.mean_in_range[0]}, {self.mean_in_range[1]}]'

    def validate(self, data: pd.Series) -> base.ValidationResult:
        dataset_mean = data.mean()
        min_, max_ = self.mean_in_range
        passes = min_ <= dataset_mean <= max_
        return base.ValidationResult(
            passes=passes,
            message=f"Dataset has mean: {dataset_mean}. This {'is ' if passes else 'is not '} "
                    f'in the required range: [{self.mean_in_range[0]}, {self.mean_in_range[1]}].',
            diagnostics={
                'dataset_mean': dataset_mean,
                'mean_in_range': self.mean_in_range
            }
        )

    @classmethod
    def arg(cls) -> str:
        return 'mean_in_range'

    @classmethod
    def name(cls) -> str:
        return 'mean_in_range_validator'


AVAILABLE_DEFAULT_VALIDATORS = [
    DataInRangeValidatorPandas,
    DataInRangeValidatorPrimitives,
    PandasMaxStandardDevValidator,
    PandasMeanInRangeValidator,
    DataTypeValidatorPandas,
    MaxFractionNansValidatorPandasSeries,
    NansAllowedValidatorPandas,
]


def resolve_default_validators(
        output_type: Type[Type],
        importance: str,
        available_validators: List[Type[BaseDefaultValidator]] = None,
        **default_validator_kwargs) -> List[BaseDefaultValidator]:
    """Resolves default validators given a set pof parameters and the type to which they apply.
    Note that each (kwarg, type) combination should map to a validator
    @param importance: importance level of the validator to instantiate
    @param output_type: The type to which the validator should apply
    @param available_validators: The available validators to choose from
    @param default_validator_kwargs: Kwargs to use
    @return: A list of validators to use
    """
    if available_validators is None:
        available_validators = AVAILABLE_DEFAULT_VALIDATORS
    validators = []
    for key in default_validator_kwargs.keys():
        for validator_cls in available_validators:
            if key == validator_cls.arg() and validator_cls.applies_to(output_type):
                validators.append(validator_cls(**{key: default_validator_kwargs[key], 'importance': importance}))
                break
        else:
            raise ValueError(f'No registered subclass of BaseDefaultValidator is available '
                             f'for arg: {key} and type {output_type}. This either means (a) this arg-type '
                             f"contribution isn't supported or (b) this has not been added yet (but should be). "
                             f'In the case of (b), we welcome contributions. Get started at github.com/stitchfix/hamilton')
    return validators
