export function hasCjk(text = '') {
  return /[\u3400-\u9fff]/.test(text);
}

export function formatNumber(value, digits = 3) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value ?? '—');
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(number);
}

export function friendlyField(name = '', chinese = false) {
  const labels = chinese ? {
    population: '人口',
    bachelor_pct: '本科及以上人口比例',
    bachelor_percent: '本科及以上人口比例',
    bachelor_percentage: '本科及以上人口比例',
    bachelors_or_higher_pct: '本科及以上人口比例',
    bachelors_or_higher_percent: '本科及以上人口比例',
    edu_pct: '本科及以上人口比例',
    median_salary: '中位工资',
    city_name: '城市',
    name: '名称',
    state: '州',
    count: '样本数',
    min: '最小值',
    max: '最大值',
    mean: '均值',
    median: '中位数',
    pearson_r: 'Pearson r',
  } : {
    population: 'Population',
    bachelor_pct: "Bachelor’s degree or higher",
    bachelor_percent: "Bachelor’s degree or higher",
    bachelor_percentage: "Bachelor’s degree or higher",
    bachelors_or_higher_pct: "Bachelor’s degree or higher",
    bachelors_or_higher_percent: "Bachelor’s degree or higher",
    edu_pct: "Bachelor’s degree or higher",
    median_salary: 'Median salary',
    city_name: 'City',
    name: 'Name',
  };
  return labels[name] || String(name).replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function friendlyOperation(name = '', chinese = false) {
  const labels = chinese ? {
    descriptive_stats: '描述统计',
    correlation: 'Pearson 相关性',
    percent_change: '百分比变化',
    percentile: '百分位数',
  } : {
    descriptive_stats: 'Descriptive statistics',
    correlation: 'Pearson correlation',
    percent_change: 'Percent change',
    percentile: 'Percentile',
  };
  return labels[name] || friendlyField(name, chinese);
}

export function isPercentageField(name = '') {
  return /(pct|percent|percentage|ratio|share)/i.test(name);
}

export function formatDisplayValue(value, column = '', digits = 3) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value ?? '—');
  if (/(^|_)year$|_id$|^id$/i.test(column)) return String(value);
  if (isPercentageField(column)) return `${formatNumber(number, 2)}%`;
  return formatNumber(number, digits);
}

export function niceScale(min, max, count = 5, { includeZero = false } = {}) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return { min, max, ticks: [] };
  if (min === max) {
    const pad = Math.max(Math.abs(min) * 0.1, 1);
    min -= pad;
    max += pad;
  }
  if (includeZero) {
    min = Math.min(0, min);
    max = Math.max(0, max);
  }
  const span = Math.max(max - min, Number.EPSILON);
  const rawStep = span / Math.max(1, count - 1);
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 2.5 ? 2.5 : normalized <= 5 ? 5 : 10;
  const step = nice * magnitude;
  const niceMin = Math.floor(min / step) * step;
  const niceMax = Math.ceil(max / step) * step;
  const ticks = [];
  for (let value = niceMin; value <= niceMax + step * 0.001; value += step) {
    const rounded = Math.abs(value) < step * 1e-9 ? 0 : Number(value.toPrecision(12));
    ticks.push(rounded);
  }
  return { min: niceMin, max: niceMax, ticks: ticks.slice(0, 8) };
}

export function tokenizeInlineMarkdown(text = '') {
  const value = String(text ?? '');
  return value
    .split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*|_[^_\n]+_)/g)
    .filter(Boolean)
    .map(part => {
      if (part.startsWith('**') && part.endsWith('**')) return { type: 'strong', text: part.slice(2, -2) };
      if (part.startsWith('`') && part.endsWith('`')) return { type: 'code', text: part.slice(1, -1) };
      if ((part.startsWith('*') && part.endsWith('*')) || (part.startsWith('_') && part.endsWith('_'))) {
        return { type: 'em', text: part.slice(1, -1) };
      }
      return { type: 'text', text: part };
    });
}
