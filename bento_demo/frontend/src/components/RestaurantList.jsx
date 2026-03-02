import React from 'react';
import { motion } from 'framer-motion';
import { Store, Star, Clock } from 'lucide-react';

const AVATAR_COLORS = [
    '#F59E0B', '#3B82F6', '#10B981', '#8B5CF6',
    '#EF4444', '#EC4899', '#14B8A6', '#F97316',
];

export default function RestaurantList({ restaurants, selectedId, onSelect }) {
    return (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA] overflow-hidden flex flex-col">
            <div className="flex items-center gap-2 mb-4">
                <Store size={16} className="text-[#E23744]" />
                <p className="text-[11px] font-semibold uppercase tracking-widest text-gray-400">Restaurants</p>
            </div>

            <div className="overflow-y-auto flex-grow pr-1 hide-scrollbar space-y-2">
                {restaurants.map((r, i) => {
                    const isSelected = r.restaurant_id === selectedId;
                    const color = AVATAR_COLORS[i % AVATAR_COLORS.length];
                    const initials = r.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

                    return (
                        <motion.div
                            key={r.restaurant_id}
                            whileHover={{ scale: 1.01 }}
                            onClick={() => onSelect(r.restaurant_id)}
                            className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all
                ${isSelected
                                    ? 'bg-white border-l-4 border-[#E23744] shadow-md'
                                    : 'bg-gray-50 border-l-4 border-transparent hover:bg-white hover:shadow-sm'}`}
                        >
                            {/* Avatar */}
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                                style={{ background: color }}>
                                {initials}
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                                <p className={`text-sm font-semibold truncate ${isSelected ? 'text-gray-800' : 'text-gray-600'}`}>
                                    {r.name}
                                </p>
                                <p className="text-[11px] text-gray-400 truncate">
                                    {r.cuisine_primary} • {r.city}
                                </p>
                                <div className="flex items-center gap-3 text-[10px] text-gray-400 mt-0.5">
                                    <span className="flex items-center gap-0.5">
                                        <Clock size={10} /> {20 + Math.floor(Math.random() * 20)}m
                                    </span>
                                    <span>• ₹{r.price_range === 'budget' ? '150' : r.price_range === 'mid' ? '350' : '500'} for two</span>
                                </div>
                            </div>

                            {/* Rating */}
                            <div className={`flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-bold
                ${r.avg_rating >= 4.0 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                {r.avg_rating.toFixed(1)}
                                <Star size={10} fill="currentColor" />
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}
