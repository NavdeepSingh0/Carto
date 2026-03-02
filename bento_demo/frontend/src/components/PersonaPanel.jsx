import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Tag, MapPin, Leaf, Sun, ShoppingCart, X, Clock } from 'lucide-react';

const SEGMENTS = [
    { key: 'budget', label: 'Budget', icon: '💰', aov: '~₹200' },
    { key: 'mid', label: 'Mid', icon: '💎', aov: '~₹450' },
    { key: 'premium', label: 'Premium', icon: '👑', aov: '~₹750' },
];

const MEAL_TIMES = [
    { key: 'breakfast', label: 'Breakfast', time: '8–11 AM' },
    { key: 'lunch', label: 'Lunch', time: '12–3 PM' },
    { key: 'snacks', label: 'Snacks', time: '4–6 PM' },
    { key: 'dinner', label: 'Dinner', time: '7–11 PM' },
];

export default function PersonaPanel({ profile, onProfileChange, cart, onRemoveFromCart, cartValue, headroom, cities }) {
    return (
        <>
            {/* PERSONA */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA]">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 mb-3">Persona</p>
                <div className="flex gap-2">
                    {SEGMENTS.map(s => (
                        <button key={s.key}
                            onClick={() => onProfileChange('segment', s.key)}
                            className={`flex-1 px-2 py-2 rounded-xl text-xs font-semibold transition-all
                ${profile.segment === s.key
                                    ? 'bg-[#E23744]/10 text-[#E23744] border-2 border-[#E23744] shadow-sm'
                                    : 'bg-gray-50 text-gray-500 border-2 border-transparent hover:bg-gray-100'}`}>
                            <span className="text-sm mr-1">{s.icon}</span>
                            {s.label}
                            <div className="text-[10px] text-gray-400 mt-0.5">{s.aov}</div>
                        </button>
                    ))}
                </div>
            </div>

            {/* LOCATION */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA]">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 mb-3">Location</p>
                <div className="relative">
                    <MapPin size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <select
                        value={profile.city}
                        onChange={e => onProfileChange('city', e.target.value)}
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white border border-gray-200 text-sm font-medium text-gray-700 appearance-none cursor-pointer hover:border-[#E23744]/40 transition-colors focus:outline-none focus:border-[#E23744]"
                    >
                        {(cities || []).map(c => (
                            <option key={c} value={c}>{c}</option>
                        ))}
                    </select>
                    <MapPin size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#E23744]" />
                </div>
            </div>

            {/* VEG / NON-VEG */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA]">
                <div className="flex rounded-xl overflow-hidden border border-gray-200">
                    <button
                        onClick={() => onProfileChange('is_veg', true)}
                        className={`flex-1 py-2.5 text-xs font-bold flex items-center justify-center gap-1.5 transition-all
              ${profile.is_veg
                                ? 'bg-green-50 text-green-700 border-r border-green-200'
                                : 'bg-white text-gray-400 border-r border-gray-200 hover:bg-gray-50'}`}>
                        <span className="w-3 h-3 rounded-sm border-2 border-green-600 bg-green-600 inline-block" /> VEG
                    </button>
                    <button
                        onClick={() => onProfileChange('is_veg', false)}
                        className={`flex-1 py-2.5 text-xs font-bold flex items-center justify-center gap-1.5 transition-all
              ${!profile.is_veg
                                ? 'bg-red-50 text-red-600'
                                : 'bg-white text-gray-400 hover:bg-gray-50'}`}>
                        <span className="w-3 h-3 rounded-sm border-2 border-red-500 bg-red-500 inline-block" /> NON-VEG
                    </button>
                </div>
            </div>

            {/* MEAL TIME */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA]">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 mb-3">
                    <Clock size={12} className="inline mr-1" />Meal Time
                </p>
                <div className="flex gap-2 flex-wrap">
                    {MEAL_TIMES.map(mt => (
                        <button key={mt.key}
                            onClick={() => onProfileChange('meal_time', mt.key)}
                            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all
                ${profile.meal_time === mt.key
                                    ? 'bg-[#E23744] text-white shadow-sm'
                                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
                            {mt.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* YOUR ORDER */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA] flex-grow">
                <div className="flex items-center justify-between mb-3">
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-[#E23744]">Your Order</p>
                    {cart.length > 0 && (
                        <span className="text-xs font-bold text-gray-400">{cart.length} item{cart.length > 1 ? 's' : ''}</span>
                    )}
                </div>

                <AnimatePresence mode="popLayout">
                    {cart.length === 0 ? (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-8 text-gray-300">
                            <ShoppingCart size={32} className="mx-auto mb-2" />
                            <p className="text-sm font-medium text-gray-400">Your cart is empty</p>
                            <p className="text-xs text-gray-300 mt-1">Add items from the menu</p>
                        </motion.div>
                    ) : (
                        <>
                            {cart.map(item => (
                                <motion.div
                                    key={item.item_id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 group"
                                >
                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${item.is_veg ? 'bg-green-500' : 'bg-red-500'}`} />
                                        <div className="min-w-0">
                                            <p className="text-xs font-medium text-gray-700 truncate">x1 {item.item_name}</p>
                                            <p className="text-[10px] text-gray-400">{item.category}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-gray-600">₹{item.price}</span>
                                        <button
                                            onClick={() => onRemoveFromCart(item.item_id)}
                                            className="opacity-0 group-hover:opacity-100 w-5 h-5 rounded-full bg-red-50 text-red-400 flex items-center justify-center hover:bg-red-100 transition-all"
                                        >
                                            <X size={10} />
                                        </button>
                                    </div>
                                </motion.div>
                            ))}

                            {/* Total + Headroom */}
                            <div className="mt-3 pt-3 border-t border-dashed border-gray-200">
                                <div className="flex justify-between text-sm font-bold">
                                    <span className="text-gray-600">Total</span>
                                    <span className="text-gray-800">₹{cartValue}</span>
                                </div>
                                {headroom > 0 && (
                                    <div className="flex justify-between text-xs mt-1.5">
                                        <span className="text-gray-400">Available Budget</span>
                                        <span className={`font-bold ${headroom > 200 ? 'text-green-600' : headroom > 50 ? 'text-amber-500' : 'text-red-500'}`}>
                                            ₹{headroom.toFixed(0)}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </AnimatePresence>
            </div>
        </>
    );
}
