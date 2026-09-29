import React from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, ShieldCheck, Cpu, RefreshCw, Heart } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-neutral-900 text-neutral-300 pt-16 pb-12 border-t border-neutral-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          {/* Brand Info */}
          <div className="space-y-4 md:col-span-1">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="font-serif text-xl font-bold text-white tracking-tight">
                Style<span className="text-indigo-400">Sense</span>
              </span>
            </Link>
            <p className="text-xs text-neutral-400 leading-relaxed">
              AI-powered personalized fashion product discovery platform using hybrid content-based and collaborative recommendation systems.
            </p>
            <div className="flex items-center gap-2 text-xs text-indigo-400 font-medium">
              <Cpu className="w-3.5 h-3.5" />
              <span>TF-IDF • Cosine Similarity • Hybrid CF</span>
            </div>
          </div>

          {/* Catalog Categories */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-4">
              Explore Collections
            </h4>
            <ul className="space-y-2 text-xs text-neutral-400">
              <li>
                <Link to="/products?category=Topwear" className="hover:text-white transition-colors">
                  Topwear & Shirts
                </Link>
              </li>
              <li>
                <Link to="/products?category=Bottomwear" className="hover:text-white transition-colors">
                  Bottomwear & Denim
                </Link>
              </li>
              <li>
                <Link to="/products?category=Ethnic" className="hover:text-white transition-colors">
                  Ethnic Wear & Sarees
                </Link>
              </li>
              <li>
                <Link to="/products?category=Footwear" className="hover:text-white transition-colors">
                  Footwear & Sneakers
                </Link>
              </li>
              <li>
                <Link to="/products?category=Bags" className="hover:text-white transition-colors">
                  Bags & Backpacks
                </Link>
              </li>
            </ul>
          </div>

          {/* AI Features */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-4">
              AI Recommendation Features
            </h4>
            <ul className="space-y-2 text-xs text-neutral-400">
              <li className="flex items-center gap-2">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                Personalized Style Feed
              </li>
              <li className="flex items-center gap-2">
                <RefreshCw className="w-3 h-3 text-indigo-400" />
                Real-Time Interaction Tuning
              </li>
              <li className="flex items-center gap-2">
                <Heart className="w-3 h-3 text-indigo-400" />
                Wishlist-Driven Discovery
              </li>
              <li className="flex items-center gap-2">
                <ShieldCheck className="w-3 h-3 text-indigo-400" />
                Diversity Re-Ranking (MMR)
              </li>
            </ul>
          </div>

          {/* Technology & Student Info */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-4">
              Technical Stack
            </h4>
            <p className="text-xs text-neutral-400 leading-relaxed mb-3">
              Built with React, Vite, Tailwind CSS, Flask, MongoDB Atlas, and Scikit-Learn.
            </p>
            <div className="p-3 rounded-xl bg-neutral-800/80 border border-neutral-700/60 text-[11px] text-neutral-300">
              <span className="font-semibold text-white block mb-1">Portfolio Project</span>
              Designed for SDE Intern & Full-Stack Machine Learning engineering roles.
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-neutral-800 text-center sm:flex sm:justify-between text-xs text-neutral-500">
          <p>© {new Date().getFullYear()} StyleSense. Original fashion recommendation system.</p>
          <p className="mt-2 sm:mt-0">Designed & Engineered with Python, Flask, MongoDB & React.</p>
        </div>
      </div>
    </footer>
  )
}
