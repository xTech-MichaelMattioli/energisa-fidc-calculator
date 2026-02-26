/**
 * Service: Field Mapper
 * Automatic and manual mapping of source columns to standard schema.
 */
import type { FieldMapping, RawRecord, MappedRecord } from "@/types";

/** Standard target fields with synonyms for auto-mapping */
const FIELD_SYNONYMS: Record<string, string[]> = {
  empresa: ["empresa", "distribuidora", "company", "cod_empresa", "nome_empresa"],
  tipo: ["tipo", "tipo_consumidor", "type", "categoria", "tipo_cliente"],
  status: ["status", "situacao_conta", "status_conta", "state"],
  situacao: ["situacao", "situação", "situaçao", "situacão", "sit", "situacao_especifica"],
  nome_cliente: ["nome_cliente", "cliente", "nome", "client_name", "consumidor", "nome_consumidor"],
  documento: ["documento", "cpf_cnpj", "cpf", "cnpj", "doc", "nr_documento"],
  classe: ["classe", "class", "classificacao", "classe_consumo", "categoria"],
  contrato: ["contrato", "uc", "unidade_consumidora", "contract", "nr_uc", "instalacao", "conta", "vinculado"],
  valor_principal: ["valor_principal", "valor", "value", "vl_principal", "principal", "fatura", "faturas"],
  valor_nao_cedido: ["valor_nao_cedido", "nao_cedido", "vl_nao_cedido", "cedido"],
  valor_terceiro: ["valor_terceiro", "terceiro", "vl_terceiro", "terceiros"],
  valor_cip: ["valor_cip", "cip", "cosip", "vl_cip", "cips"],
  data_vencimento: ["data_vencimento", "vencimento", "due_date", "dt_vencimento", "data_venc", "prazo", "venc"],
};

/**
 * Automatically map source columns to target fields using fuzzy matching.
 */
export function autoMapFields(sourceColumns: string[]): FieldMapping {
  const mapping: FieldMapping = {};
  const normalizedSources = sourceColumns.map((c) =>
    c.toLowerCase().replace(/[\s_-]+/g, "_").trim()
  );

  for (const [target, synonyms] of Object.entries(FIELD_SYNONYMS)) {
    for (const syn of synonyms) {
      const idx = normalizedSources.findIndex(
        (s) => s === syn || s.includes(syn) || syn.includes(s)
      );
      if (idx !== -1 && !Object.values(mapping).includes(sourceColumns[idx])) {
        mapping[target] = sourceColumns[idx];
        break;
      }
    }
  }

  return mapping;
}

/**
 * Get the list of required fields that are not yet mapped.
 */
export function getMissingRequiredFields(mapping: FieldMapping): string[] {
  const required = [
    "empresa",
    "tipo",
    "valor_principal",
    "data_vencimento",
  ];
  return required.filter((f) => !mapping[f]);
}

/**
 * Get confidence score for a mapping (0-100).
 */
export function getMappingConfidence(mapping: FieldMapping): number {
  const allFields = Object.keys(FIELD_SYNONYMS);
  const mapped = allFields.filter((f) => !!mapping[f]);
  return Math.round((mapped.length / allFields.length) * 100);
}

/**
 * Apply mapping to raw records, producing standardized MappedRecords.
 */
export function applyMapping(
  records: RawRecord[],
  mapping: FieldMapping,
  options: {
    dataBase: string;
    baseOrigem: string;
    isVoltz: boolean;
  }
): MappedRecord[] {
  return records.map((raw) => {
    const get = (field: string): unknown => {
      const sourceCol = mapping[field];
      return sourceCol ? raw[sourceCol] : undefined;
    };

    const toNumber = (val: unknown): number => {
      if (typeof val === "number") return val;
      const n = Number(String(val).replace(/[^\d.,-]/g, "").replace(",", "."));
      return isNaN(n) ? 0 : n;
    };

    const toString = (val: unknown): string =>
      val != null ? String(val).trim() : "";

    return {
      empresa: options.isVoltz ? "VOLTZ" : toString(get("empresa")),
      tipo: toString(get("tipo")) || "Privado",
      status: toString(get("status")),
      situacao: toString(get("situacao")),
      nome_cliente: toString(get("nome_cliente")),
      documento: toString(get("documento")),
      classe: toString(get("classe")),
      contrato: toString(get("contrato")),
      valor_principal: toNumber(get("valor_principal")),
      valor_nao_cedido: options.isVoltz ? 0 : toNumber(get("valor_nao_cedido")),
      valor_terceiro: options.isVoltz ? 0 : toNumber(get("valor_terceiro")),
      valor_cip: options.isVoltz ? 0 : toNumber(get("valor_cip")),
      data_vencimento: toString(get("data_vencimento")),
      data_base: options.dataBase,
      base_origem: options.baseOrigem,
    };
  });
}

/** All target field names */
export const TARGET_FIELDS = Object.keys(FIELD_SYNONYMS);
