from typing import Any, Dict, Type

from pydantic import BaseModel


def pydantic_to_markdown(model: Type[BaseModel]) -> str:
    """
    Pydanticモデルクラスからマークダウン形式の文字列を生成する
    モデルの各フィールド名とdescriptionを取得し、階層構造を再帰的に表現する。
    これはllmのプロンプトとして使うことを想定している。

    :param model: Pydanticモデルクラス
    :return: マークダウン形式の文字列
    """

    def schema_to_markdown(
        schema: Dict[str, Any],
        indent: int = 0,
        all_defs: Dict[str, Any] = None,
    ) -> str:
        """
        与えられたPydanticモデルのスキーマ(dict)から、キー構造と各キーのdescriptionを
        再帰的にたどってマークダウン形式で文字列に整形する。
        ネストされたプロパティや`$ref`による参照も処理し、階層構造を出力する。

        :param schema: model_json_schema() または schema() で得られる辞書
        :param indent: インデント用のスペース
        :param all_defs: スキーマ内に定義された $ref 解決用の定義（definitions / $defs）
        :return: マークダウン形式の文字列
        """

        # もし最上位で呼び出された場合、definitions($defs)を抜き出しておく
        # Pydantic v2: "definitions" => "$defs" の場合もある
        if all_defs is None:
            all_defs = schema.get("definitions") or schema.get("$defs") or {}

        # $refがあれば解決してそのスキーマに置き換える
        if "$ref" in schema:
            ref = schema["$ref"]
            ref_key = ref.split("/")[-1]  # "#/definitions/SomeModel" → "SomeModel"
            ref_schema = all_defs.get(ref_key, {})
            # 参照先にもさらに$refがある場合があるので再帰で処理
            return schema_to_markdown(ref_schema, indent, all_defs)

        lines = []
        prefix = "  " * indent + "- "

        # プロパティ一覧を取得
        properties = schema.get("properties", {})
        # required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            # $refがある場合は参照を解決
            if "$ref" in prop_schema:
                # 参照スキーマを取得
                ref = prop_schema["$ref"]
                ref_key = ref.split("/")[-1]
                nested_schema = all_defs.get(ref_key, {})
            else:
                nested_schema = prop_schema

            # 必須かどうか
            # req_mark = " **(必須)**" if prop_name in required else ""

            # 説明文
            description = nested_schema.get("description", "").strip()
            # line = f"{prefix}**{prop_name}**:{req_mark} {description}"
            line = f"{prefix}{prop_name}: {description}"
            lines.append(line)

            # typeを見て再帰的に処理
            t = nested_schema.get("type", None)

            # object 型の場合
            if t == "object":
                lines.append(schema_to_markdown(nested_schema, indent + 1, all_defs))

            # array 型の場合
            elif t == "array":
                items = nested_schema.get("items", {})
                # $refがあればここで解決
                if "$ref" in items:
                    ref = items["$ref"]
                    ref_key = ref.split("/")[-1]
                    items = all_defs.get(ref_key, {})

                # 配列要素がobjectの場合はさらに再帰
                if items.get("type") == "object" or "$ref" in items:
                    lines.append(schema_to_markdown(items, indent + 1, all_defs))

        return "\n".join(lines)

    schema = model.model_json_schema()
    return schema_to_markdown(schema)
