import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Plus, ShoppingBag } from 'lucide-react';

const NODE_COLORS = {
    Node1_Extension: { bg: '#FFF7ED', text: '#FB923C', label: '1 Extension' },
    Node2_Texture: { bg: '#F5F3FF', text: '#A78BFA', label: '2 Texture' },
    Node3_CoOccurrence: { bg: '#EFF6FF', text: '#38BDF8', label: '3 CoOccur' },
    Node4_Beverage: { bg: '#ECFDF5', text: '#34D399', label: '4 Beverage' },
    Node5_Dessert: { bg: '#FDF2F8', text: '#F472B6', label: '5 Dessert' },
    Node6_BudgetHabit: { bg: '#FFFBEB', text: '#F59E0B', label: '6 Budget' },
};

const FOOD_GRADIENTS = {
    Beverage: 'linear-gradient(135deg, #34D39940, #059669)',
    Dessert: 'linear-gradient(135deg, #F472B640, #DB2777)',
    Extension: 'linear-gradient(135deg, #FB923C40, #EA580C)',
    Side: 'linear-gradient(135deg, #A78BFA40, #7C3AED)',
    Main: 'linear-gradient(135deg, #E2374440, #BE123C)',
    Starter: 'linear-gradient(135deg, #38BDF840, #0284C7)',
};

export default function PairsWellRail({ recommendations, cart, onAddToCart }) {
    return (
        <div className="bento-card p-6 relative overflow-hidden">
            {/* Decorative glow */}
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"
                style={{ background: 'rgba(245,184,0,0.05)' }}></div>

            {/* Header */}
            <div className="flex items-center gap-3 mb-5 relative z-10">
                <h3 className="section-label">Pairs Well With This</h3>
                <span className="text-white text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm"
                    style={{ background: 'linear-gradient(to right, #F5B800, #FB923C)' }}>
                    <Sparkles size={10} /> AI PICK
                </span>
            </div>

            {/* Content */}
            <div className="relative z-10">
                {cart.length === 0 || recommendations.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                        <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
                            <ShoppingBag size={20} className="text-gray-400" />
                        </div>
                        <p className="text-xs text-gray-400 font-medium">Add items to see recommendations</p>
                    </div>
                ) : (
                    <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide snap-x snap-mandatory">
                        <AnimatePresence>
                            {recommendations.map((rec, idx) => {
                                const inCart = cart.some(c => c.item_id === rec.item_id);
                                const node = NODE_COLORS[rec.hexagon_node] || { bg: '#F3F4F6', text: '#6B7280', label: rec.hexagon_node };
                                const matchPct = Math.round((rec.score || 0) * 100);
                                const gradient = FOOD_GRADIENTS[rec.category] || FOOD_GRADIENTS.Main;

                                return (
                                    <motion.div
                                        key={rec.item_id}
                                        initial={{ opacity: 0, scale: 0.9, y: 10 }}
                                        animate={{ opacity: 1, scale: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        transition={{ delay: idx * 0.08, type: 'spring', stiffness: 200, damping: 20 }}
                                        whileHover={{ y: -4, boxShadow: '0 20px 40px -10px rgba(0,0,0,0.08)' }}
                                        className="min-w-[160px] max-w-[160px] bg-white p-2.5 rounded-2xl border border-gray-100 shadow-sm cursor-pointer group snap-start flex-shrink-0"
                                    >
                                        {/* Food image placeholder */}
                                        <div className="h-24 rounded-xl overflow-hidden mb-2.5 relative"
                                            style={{ background: gradient }}>
                                            <div className="absolute inset-0 flex items-center justify-center">
                                                <span className="text-white/60 text-3xl">
                                                    {rec.category === 'Beverage' ? '🥤' : rec.category === 'Dessert' ? '🍰' : rec.category === 'Extension' ? '🫓' : rec.category === 'Side' ? '🥗' : '🍛'}
                                                </span>
                                            </div>
                                            {/* Match badge */}
                                            <div className="absolute top-1.5 right-1.5 bg-black/70 backdrop-blur-md text-white text-[9px] font-bold px-1.5 py-0.5 rounded-md border border-white/10">
                                                {matchPct}% Match
                                            </div>
                                        </div>

                                        {/* Hexagon node badge */}
                                        <div className="mb-1.5">
                                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md"
                                                style={{ background: node.bg, color: node.text }}>
                                                ○ {node.label}
                                            </span>
                                        </div>

                                        {/* Name + Price + Add */}
                                        <div className="flex justify-between items-start">
                                            <div className="min-w-0">
                                                <h4 className="font-bold text-xs truncate" style={{ color: 'var(--color-zomato-charcoal)', maxWidth: '100px' }}>
                                                    {rec.item_name}
                                                </h4>
                                                <span className="text-[10px] text-gray-500 font-mono">₹{rec.price}</span>
                                            </div>
                                            {inCart ? (
                                                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                                                    <span className="text-green-600 text-[10px] font-bold">✓</span>
                                                </div>
                                            ) : (
                                                <motion.button
                                                    whileHover={{ scale: 1.15 }}
                                                    whileTap={{ scale: 0.9 }}
                                                    onClick={() => onAddToCart(rec)}
                                                    className="w-6 h-6 rounded-full bg-gray-50 flex items-center justify-center hover:bg-[#E23744] hover:text-white transition-colors flex-shrink-0 cursor-pointer"
                                                    style={{ color: '#E23744' }}
                                                >
                                                    <Plus size={14} />
                                                </motion.button>
                                            )}
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </AnimatePresence>
                    </div>
                )}
            </div>
        </div>
    );
}
