"""Gradient Finetuning."""

import json
from typing import Any, Optional, overload

from llama_index.finetuning.types import BaseLLMFinetuneEngine
from llama_index.llms.gradient import GradientModelAdapterLLM


class GradientFinetuneEngine(BaseLLMFinetuneEngine):
    @overload
    def __init__(
        self,
        *,
        access_token: Optional[str] = None,
        base_model_slug: str,
        data_path: str,
        host: Optional[str] = None,
        learning_rate: Optional[float] = None,
        name: str,
        rank: Optional[int] = None,
        workspace_id: Optional[str] = None,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        access_token: Optional[str] = None,
        data_path: str,
        host: Optional[str] = None,
        model_adapter_id: str,
        workspace_id: Optional[str] = None,
    ) -> None:
        ...

    def __init__(
        self,
        *,
        access_token: Optional[str] = None,
        base_model_slug: Optional[str] = None,
        data_path: str,
        host: Optional[str] = None,
        learning_rate: Optional[float] = None,
        model_adapter_id: Optional[str] = None,
        name: Optional[str] = None,
        rank: Optional[int] = None,
        workspace_id: Optional[str] = None,
    ) -> None:
        self._access_token = access_token
        self._host = host
        self._workspace_id = workspace_id
        self._data_path = data_path

        if (base_model_slug is None and model_adapter_id is None) or (
            isinstance(base_model_slug, str) and isinstance(model_adapter_id, str)
        ):
            raise ValueError(
                "expected be provided exactly one of base_model_slug or model_adapter_id"
            )
        try:
            from gradientai import Gradient

            self._gradient = Gradient(
                access_token=access_token, host=host, workspace_id=workspace_id
            )
            if isinstance(base_model_slug, str):
                if name is None:
                    raise ValueError("name must be provided with a base_model_slug")
                self._model_adapter = self._gradient.get_base_model(
                    base_model_slug=base_model_slug
                ).create_model_adapter(
                    name=name, rank=rank, learning_rate=learning_rate
                )
            if isinstance(model_adapter_id, str):
                self._model_adapter = self._gradient.get_model_adapter(
                    model_adapter_id=model_adapter_id
                )

        except ImportError as e:
            raise ImportError(
                "Could not import Gradient Python package. "
                "Please install it with `pip install gradientai`."
            ) from e

    def close(self) -> None:
        self._gradient.close()

    def finetune(self) -> None:
        from gradientai import Sample

        with open(self._data_path) as f:
            for [i, line] in enumerate(f):
                parsedLine = json.loads(line)
                if not isinstance(parsedLine, dict):
                    raise ValueError(
                        f"each line should be a json object. line {i + 1} does not parse correctly"
                    )
                sample = Sample(
                    inputs=parsedLine["inputs"],
                    multiplier=parsedLine.get("multiplier", None),
                )
                self._model_adapter.fine_tune(samples=[sample])

    def get_finetuned_model(self, **model_kwargs: Any) -> GradientModelAdapterLLM:
        return GradientModelAdapterLLM(
            access_token=self._access_token,
            host=self._host,
            model_adapter_id=self._model_adapter.id,
            workspace_id=self._workspace_id,
            **model_kwargs,
        )
