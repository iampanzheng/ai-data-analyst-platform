import test from 'node:test';
import assert from 'node:assert/strict';
import {
  formatDisplayValue,
  friendlyField,
  friendlyOperation,
  niceScale,
  tokenizeInlineMarkdown,
} from '../src/presentation.js';

test('formats population and percentage fields for display only', () => {
  assert.equal(formatDisplayValue(8584629, 'population'), '8,584,629');
  assert.equal(formatDisplayValue('42.5000', 'bachelor_percent'), '42.5%');
  assert.equal(formatDisplayValue(2025, 'year'), '2025');
});

test('maps analysis fields and operations to presentation labels', () => {
  assert.equal(friendlyField('bachelor_percent', true), '本科及以上人口比例');
  assert.equal(friendlyOperation('correlation', true), 'Pearson 相关性');
  assert.equal(friendlyOperation('descriptive_stats', false), 'Descriptive statistics');
});

test('nice scale rounds chart domains and ticks', () => {
  const scale = niceScale(1665481, 8584629, 5);
  assert.ok(scale.min <= 1665481);
  assert.ok(scale.max >= 8584629);
  assert.ok(scale.ticks.length >= 4);
  assert.ok(scale.ticks.every(Number.isFinite));
});

test('inline markdown tokenization preserves safe emphasis semantics', () => {
  assert.deepEqual(tokenizeInlineMarkdown('This is *italic*, **bold**, and `code`.'), [
    { type: 'text', text: 'This is ' },
    { type: 'em', text: 'italic' },
    { type: 'text', text: ', ' },
    { type: 'strong', text: 'bold' },
    { type: 'text', text: ', and ' },
    { type: 'code', text: 'code' },
    { type: 'text', text: '.' },
  ]);
});
