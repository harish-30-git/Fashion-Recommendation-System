import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SlidersHorizontal, X, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { productService } from '../services/productService'
import ProductGrid from '../components/product/ProductGrid'
import ProductFilters from '../components/product/ProductFilters'
import ErrorMessage from '../components/common/ErrorMessage'

export default function ProductListPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const [products, setProducts] = useState([])
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0, per_page: 20 })
  const [categories, setCategories] = useState([])
  const [brands, setBrands] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false)

  // Current filters extracted from URL params
  const currentFilters = {
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
    gender: searchParams.get('gender') || '',
    brand: searchParams.get('brand') || '',
    min_price: searchParams.get('min_price') ? Number(searchParams.get('min_price')) : null,
    max_price: searchParams.get('max_price') ? Number(searchParams.get('max_price')) : null,
    sort_by: searchParams.get('sort_by') || 'popularity',
    page: searchParams.get('page') ? Number(searchParams.get('page')) : 1,
  }

  // Load filter options once
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [cats, brs] = await Promise.all([
          productService.getCategories(),
          productService.getBrands(),
        ])
        setCategories(cats)
        setBrands(brs)
      } catch {
        // Fallback filter lists
      }
    }
    fetchMetadata()
  }, [])

  // Fetch products whenever searchParams change
  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = {
          page: currentFilters.page,
          per_page: 20,
          sort_by: currentFilters.sort_by,
        }
        if (currentFilters.category) params.category = currentFilters.category
        if (currentFilters.gender) params.gender = currentFilters.gender
        if (currentFilters.brand) params.brand = currentFilters.brand
        if (currentFilters.min_price) params.min_price = currentFilters.min_price
        if (currentFilters.max_price) params.max_price = currentFilters.max_price

        let res
        if (currentFilters.q) {
          res = await productService.searchProducts(currentFilters.q, params)
        } else {
          res = await productService.getProducts(params)
        }

        setProducts(res.data?.products || [])
        if (res.pagination) {
          setPagination(res.pagination)
        }
      } catch (err) {
        setError('Failed to load products. Please check if backend is running.')
      } finally {
        setLoading(false)
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }

    fetchProducts()
  }, [searchParams])

  const updateFilters = (newFilters) => {
    const params = new URLSearchParams()
    if (newFilters.q) params.set('q', newFilters.q)
    if (newFilters.category) params.set('category', newFilters.category)
    if (newFilters.gender) params.set('gender', newFilters.gender)
    if (newFilters.brand) params.set('brand', newFilters.brand)
    if (newFilters.min_price !== null && newFilters.min_price !== undefined)
      params.set('min_price', newFilters.min_price)
    if (newFilters.max_price !== null && newFilters.max_price !== undefined)
      params.set('max_price', newFilters.max_price)
    if (newFilters.sort_by) params.set('sort_by', newFilters.sort_by)
    if (newFilters.page && newFilters.page > 1) params.set('page', newFilters.page)

    setSearchParams(params)
  }

  const handleResetFilters = () => {
    const params = new URLSearchParams()
    if (currentFilters.q) params.set('q', currentFilters.q)
    setSearchParams(params)
  }

  const removeSingleFilter = (key) => {
    const updated = { ...currentFilters, [key]: '' }
    if (key === 'price') {
      updated.min_price = null
      updated.max_price = null
    }
    updateFilters(updated)
  }

  const handlePageChange = (newPage) => {
    updateFilters({ ...currentFilters, page: newPage })
  }

  const activeFilterTags = []
  if (currentFilters.category) {
    activeFilterTags.push({ label: `Category: ${currentFilters.category}`, key: 'category' })
  }
  if (currentFilters.gender) {
    activeFilterTags.push({ label: `Gender: ${currentFilters.gender}`, key: 'gender' })
  }
  if (currentFilters.brand) {
    activeFilterTags.push({ label: `Brand: ${currentFilters.brand}`, key: 'brand' })
  }
  if (currentFilters.min_price || currentFilters.max_price) {
    activeFilterTags.push({
      label: `Price: ₹${currentFilters.min_price || 0} - ₹${currentFilters.max_price || 'Any'}`,
      key: 'price',
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      {/* Top Header & Breadcrumb Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 gap-4 border-b border-neutral-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-neutral-900 tracking-tight">
            {currentFilters.q ? `Results for "${currentFilters.q}"` : currentFilters.category || 'All Fashion Products'}
          </h1>
          <p className="text-xs sm:text-sm text-neutral-500 mt-1">
            Showing {products.length} of {pagination.total || 0} items available in catalog
          </p>
        </div>

        {/* Mobile filter toggle button */}
        <button
          onClick={() => setMobileFilterOpen(!mobileFilterOpen)}
          className="lg:hidden inline-flex items-center gap-2 px-4 py-2.5 rounded-full border border-neutral-200 bg-white font-semibold text-xs text-neutral-800 shadow-xs"
        >
          <SlidersHorizontal className="w-4 h-4 text-indigo-600" />
          Filter & Sort {activeFilterTags.length > 0 && `(${activeFilterTags.length})`}
        </button>
      </div>

      {/* Active Filter Tags */}
      {activeFilterTags.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-4">
          <span className="text-xs font-semibold text-neutral-500">Active Filters:</span>
          {activeFilterTags.map((tag) => (
            <span
              key={tag.key}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200/80 text-xs font-medium text-indigo-700"
            >
              {tag.label}
              <button
                onClick={() => removeSingleFilter(tag.key)}
                className="hover:text-indigo-900 transition-colors"
                aria-label={`Remove filter ${tag.label}`}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
          <button
            onClick={handleResetFilters}
            className="text-xs text-neutral-400 hover:text-indigo-600 underline ml-2 transition-colors"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Main Grid + Filter Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 pt-6">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block lg:col-span-1">
          <div className="sticky top-28">
            <ProductFilters
              filters={currentFilters}
              onChange={updateFilters}
              onReset={handleResetFilters}
              categories={categories}
              brands={brands}
            />
          </div>
        </div>

        {/* Mobile Filter Drawer */}
        {mobileFilterOpen && (
          <div className="fixed inset-0 z-50 bg-black/50 lg:hidden flex justify-end">
            <div className="w-full max-w-xs bg-white h-full overflow-y-auto p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b">
                <span className="font-bold text-sm">Filter Catalog</span>
                <button onClick={() => setMobileFilterOpen(false)}>
                  <X className="w-5 h-5 text-neutral-600" />
                </button>
              </div>
              <ProductFilters
                filters={currentFilters}
                onChange={(f) => {
                  updateFilters(f)
                  setMobileFilterOpen(false)
                }}
                onReset={() => {
                  handleResetFilters()
                  setMobileFilterOpen(false)
                }}
                categories={categories}
                brands={brands}
              />
            </div>
          </div>
        )}

        {/* Product Cards Container */}
        <div className="lg:col-span-3 space-y-8">
          {error ? (
            <ErrorMessage message={error} onRetry={() => updateFilters(currentFilters)} />
          ) : (
            <ProductGrid
              products={products}
              loading={loading}
              emptyMessage="No products match your specific combination of filters. Try clearing some filters to broaden your search."
            />
          )}

          {/* Pagination Controls */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-8 border-t border-neutral-200">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={!pagination.has_prev}
                className="p-2.5 rounded-xl border border-neutral-200 hover:border-neutral-300 disabled:opacity-30 disabled:cursor-not-allowed text-neutral-700 transition-colors"
                aria-label="Previous page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="text-xs font-semibold text-neutral-600 px-3">
                Page {pagination.page} of {pagination.pages}
              </span>

              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={!pagination.has_next}
                className="p-2.5 rounded-xl border border-neutral-200 hover:border-neutral-300 disabled:opacity-30 disabled:cursor-not-allowed text-neutral-700 transition-colors"
                aria-label="Next page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
