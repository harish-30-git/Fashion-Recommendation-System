import React from 'react'
import { Filter, X, RotateCcw } from 'lucide-react'

export default function ProductFilters({
  filters,
  onChange,
  onReset,
  categories = [],
  brands = [],
}) {
  const genders = ['Men', 'Women', 'Unisex']
  const sortOptions = [
    { label: 'Popularity', value: 'popularity' },
    { label: 'Rating (High to Low)', value: 'rating' },
    { label: 'Price (Low to High)', value: 'price_asc' },
    { label: 'Price (High to Low)', value: 'price_desc' },
  ]

  const handleCategoryChange = (cat) => {
    onChange({ ...filters, category: filters.category === cat ? '' : cat, page: 1 })
  }

  const handleGenderChange = (gen) => {
    onChange({ ...filters, gender: filters.gender === gen ? '' : gen, page: 1 })
  }

  const handleBrandChange = (b) => {
    onChange({ ...filters, brand: filters.brand === b ? '' : b, page: 1 })
  }

  const handleSortChange = (e) => {
    onChange({ ...filters, sort_by: e.target.value, page: 1 })
  }

  const handlePriceChange = (min, max) => {
    onChange({ ...filters, min_price: min, max_price: max, page: 1 })
  }

  return (
    <aside className="bg-white rounded-2xl border border-neutral-200/80 p-5 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-neutral-100">
        <div className="flex items-center gap-2 font-bold text-sm text-neutral-900 uppercase tracking-wider">
          <Filter className="w-4 h-4 text-indigo-600" />
          Filters
        </div>
        <button
          onClick={onReset}
          className="text-xs text-neutral-400 hover:text-indigo-600 flex items-center gap-1 font-medium transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          Reset All
        </button>
      </div>

      {/* Sort By */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2">
          Sort By
        </label>
        <select
          value={filters.sort_by || 'popularity'}
          onChange={handleSortChange}
          className="w-full text-xs font-medium bg-neutral-50 border border-neutral-200 rounded-xl px-3 py-2 text-neutral-800 focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Gender */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2.5">
          Gender
        </label>
        <div className="flex flex-wrap gap-1.5">
          {genders.map((g) => {
            const isSelected = filters.gender === g
            return (
              <button
                key={g}
                onClick={() => handleGenderChange(g)}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${
                  isSelected
                    ? 'bg-neutral-900 text-white font-semibold shadow-xs'
                    : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200/70'
                }`}
              >
                {g}
              </button>
            )
          })}
        </div>
      </div>

      {/* Category */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2.5">
          Category
        </label>
        <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          {categories.map((cat) => {
            const isSelected = filters.category === cat
            return (
              <label
                key={cat}
                className="flex items-center gap-2 text-xs text-neutral-700 hover:text-indigo-600 cursor-pointer select-none py-0.5"
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleCategoryChange(cat)}
                  className="rounded border-neutral-300 text-indigo-600 focus:ring-indigo-500 w-3.5 h-3.5"
                />
                <span className={isSelected ? 'font-bold text-indigo-600' : ''}>{cat}</span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Price Quick Filters */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2.5">
          Price Range
        </label>
        <div className="space-y-1.5 text-xs text-neutral-600">
          {[
            { label: 'Under ₹1,000', min: null, max: 1000 },
            { label: '₹1,000 - ₹2,500', min: 1000, max: 2500 },
            { label: '₹2,500 - ₹5,000', min: 2500, max: 5000 },
            { label: 'Over ₹5,000', min: 5000, max: null },
          ].map((bracket) => {
            const isSelected =
              filters.min_price === bracket.min && filters.max_price === bracket.max
            return (
              <button
                key={bracket.label}
                onClick={() => handlePriceChange(bracket.min, bracket.max)}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                  isSelected
                    ? 'bg-indigo-50 text-indigo-700 font-bold'
                    : 'hover:bg-neutral-50 text-neutral-700'
                }`}
              >
                {bracket.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Brands (if available) */}
      {brands.length > 0 && (
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2.5">
            Brand
          </label>
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {brands.slice(0, 15).map((brand) => {
              const isSelected = filters.brand === brand
              return (
                <label
                  key={brand}
                  className="flex items-center gap-2 text-xs text-neutral-700 hover:text-indigo-600 cursor-pointer select-none py-0.5"
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleBrandChange(brand)}
                    className="rounded border-neutral-300 text-indigo-600 focus:ring-indigo-500 w-3.5 h-3.5"
                  />
                  <span className={isSelected ? 'font-bold text-indigo-600' : ''}>{brand}</span>
                </label>
              )
            })}
          </div>
        </div>
      )}
    </aside>
  )
}
