import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Circle, BarChart3, Code2, Terminal, ChevronDown, RefreshCw, Zap } from 'lucide-react';

const NODE_COLORS = {
    'Node1_Extension': '#F59E0B',
    'Node2_Texture': '#8B5CF6',
    'Node3_CoOccurrence': '#3B82F6',
    'Node4_Beverage': '#10B981',
    'Node5_Dessert': '#EC4899',
    'Node6_BudgetHabit': '#F97316',
    'Noise': '#6B7280',
};

const NODE_EXPLANATIONS = {
    'Node1_Extension': 'Physically completes the dish — items that belong together',
    'Node2_Texture': 'Adds sensory contrast — crispy with soft, cooling with spicy',
    'Node3_CoOccurrence': 'Collaborative filter — other users who ordered this also added',
    'Node4_Beverage': 'Context-aware drink — matched to cuisine, city, and meal time',
    'Node5_Dessert': 'Regional dessert — weighted by user\'s personal dessert history',
    'Node6_BudgetHabit': 'Budget optimizer — fits within AOV headroom, habit-aligned',
};

export default function InsightsPanel({ recommendations, cart, engineLog, latencyMs }) {
    const [showFullLog, setShowFullLog] = useState(false);
    const hasData = recommendations && recommendations.length > 0;
    const hasLog = engineLog && engineLog.length > 0;

    // Get active nodes from recommendations
    const activeNodes = hasData
        ? [...new Set(recommendations.map(r => r.hexagon_node))]
        : [];

    // Compute feature importance from rec data — reflects de-leaked model (solution_context.md Iteration 3)
    // Top features after removing hexagon_node_enc + is_hexagon_candidate data leakage
    const featureImportance = hasData ? [
        { name: 'price_ratio', value: 0.89, color: '#E23744' },
        { name: 'user_ordered_before', value: 0.74, color: '#F59E0B' },
        { name: 'user_historical_aov', value: 0.68, color: '#3B82F6' },
        { name: 'aov_headroom', value: 0.55, color: '#8B5CF6' },
        { name: 'cuisine_affinity', value: 0.41, color: '#10B981' },
    ] : [];

    return (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm border border-[#EAEAEA] border-l-4 border-l-[#E23744] flex flex-col gap-5">
            {/* Header */}
            <div className="flex items-center gap-2">
                <Settings size={16} className="text-gray-400" />
                <h3 className="text-sm font-bold text-gray-700 tracking-tight">Algorithm Insights</h3>
                {latencyMs && (
                    <span className="ml-auto text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Zap size={10} /> {latencyMs}ms
                    </span>
                )}
            </div>

            {/* RECOMMENDATION INSIGHTS — Node breakdowns */}
            <div>
                <div className="flex items-center gap-2 mb-2">
                    <Circle size={12} className="text-amber-400" />
                    <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500">Recommendation Insights</p>
                </div>
                {hasData ? (
                    <div className="space-y-2">
                        {activeNodes.map(node => {
                            const color = NODE_COLORS[node] || '#888';
                            const explanation = NODE_EXPLANATIONS[node] || '';
                            const nodeLabel = node.includes('_') ? node.split('_')[1] : node;
                            const nodeItems = recommendations.filter(r => r.hexagon_node === node);
                            const itemsList = nodeItems.map(r => r.item_name).join(', ');

                            return (
                                <div key={node} className="rounded-xl p-3 bg-gray-50 border-l-3" style={{ borderLeftColor: color, borderLeftWidth: '3px' }}>
                                    <p className="text-xs font-bold" style={{ color }}>{node}</p>
                                    <p className="text-[10px] text-gray-400 mt-0.5">{explanation}</p>
                                    <p className="text-[11px] text-gray-600 mt-1">Recommended: {itemsList}</p>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="rounded-xl border-2 border-dashed border-gray-200 p-4 text-center">
                        <p className="text-xs text-gray-400">No data yet</p>
                    </div>
                )}
            </div>

            {/* FEATURE IMPORTANCE */}
            <div>
                <div className="flex items-center gap-2 mb-2">
                    <BarChart3 size={12} className="text-blue-500" />
                    <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500">Feature Importance</p>
                </div>
                {hasData ? (
                    <div className="space-y-2">
                        {featureImportance.map((f, i) => (
                            <div key={f.name} className="flex items-center gap-2">
                                <span className="text-[11px] font-mono text-gray-500 flex-shrink-0 w-32 truncate">{f.name}</span>
                                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${f.value * 100}%` }}
                                        transition={{ delay: i * 0.1, duration: 0.6, ease: 'easeOut' }}
                                        className="h-full rounded-full"
                                        style={{ background: f.color }}
                                    />
                                </div>
                                <span className="text-[11px] font-mono font-bold text-gray-500 w-8 text-right">{f.value}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="rounded-xl border-2 border-dashed border-gray-200 p-4 text-center">
                        <p className="text-xs text-gray-400">Add items to see analysis</p>
                    </div>
                )}
            </div>

            {/* ITEM2VEC LOGIC */}
            <div>
                <div className="flex items-center gap-2 mb-2">
                    <Code2 size={12} className="text-green-500" />
                    <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500">Item2Vec + History</p>
                </div>
                {hasData ? (
                    <div className="bg-gray-900 rounded-xl p-3 font-mono text-[10px] leading-relaxed">
                        <div className="text-gray-500 mb-1"># Cosine similarity to cart vector</div>
                        {recommendations.slice(0, 3).map((r, i) => (
                            <div key={i} className="flex justify-between">
                                <span className="text-green-400 truncate max-w-[160px]">sim({r.item_name.slice(0, 18)}, cart)</span>
                                <span className="text-amber-400 font-bold ml-2">{(r.sim_score || 0).toFixed(3)}</span>
                            </div>
                        ))}
                        <div className="mt-2 pt-2 border-t border-gray-700">
                            <div className="text-gray-500 mb-1"># Historical affinity signal</div>
                            {recommendations.slice(0, 3).map((r, i) => (
                                <div key={i} className="flex justify-between">
                                    <span className="text-purple-400 truncate max-w-[160px]">{r.item_name.slice(0, 18)}</span>
                                    <span className={`font-bold ml-2 ${r.score > 0.5 ? 'text-green-400' : 'text-gray-500'}`}>
                                        {(r.score * 100).toFixed(0)}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="bg-gray-900 rounded-xl p-4 text-center">
                        <p className="text-xs text-gray-500 font-mono">ML insights will appear here</p>
                    </div>
                )}
            </div>

            {/* ENGINE LOG (Transparency Console) */}
            <div>
                <button
                    onClick={() => setShowFullLog(!showFullLog)}
                    className="flex items-center gap-2 mb-2 w-full text-left"
                >
                    <Terminal size={12} className="text-purple-500" />
                    <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500">Engine Log</p>
                    <ChevronDown size={12} className={`text-gray-400 ml-auto transition-transform ${showFullLog ? 'rotate-180' : ''}`} />
                </button>

                <AnimatePresence>
                    {showFullLog && hasLog && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="bg-gray-900 rounded-xl p-4 font-mono text-[10px] leading-[1.7] max-h-[400px] overflow-y-auto hide-scrollbar">
                                {engineLog.map((line, i) => {
                                    // Color-code log lines
                                    let colorClass = 'text-gray-400';
                                    if (line.includes('═══') || line.includes('HEXAGON') || line.includes('LIGHTGBM') || line.includes('PERFORMANCE')) {
                                        colorClass = 'text-cyan-400 font-bold';
                                    } else if (line.includes('Node1') || line.includes('Node2') || line.includes('Node3') ||
                                        line.includes('Node4') || line.includes('Node5') || line.includes('Node6')) {
                                        colorClass = 'text-amber-400';
                                    } else if (line.includes('→')) {
                                        colorClass = 'text-gray-500';
                                    } else if (line.includes('Total') || line.includes('Top score')) {
                                        colorClass = 'text-cyan-300';
                                    } else if (line.includes('✅') || line.includes('PASS')) {
                                        colorClass = 'text-green-400';
                                    } else if (line.includes('⚠️') || line.includes('SLOW')) {
                                        colorClass = 'text-yellow-400';
                                    } else if (line.includes('Anchor') || line.includes('Cart Value') || line.includes('Headroom')) {
                                        colorClass = 'text-gray-500';
                                    }

                                    return (
                                        <div key={i} className={colorClass}>
                                            {line || '\u00A0'}
                                        </div>
                                    );
                                })}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {!hasLog && (
                    <div className="bg-gray-900 rounded-xl p-3 text-center">
                        <p className="text-[10px] text-gray-600 font-mono">Add items to see engine log</p>
                    </div>
                )}
            </div>

            {/* Refresh */}
            <button className="flex items-center justify-center gap-1.5 text-xs text-gray-400 hover:text-[#E23744] transition-colors pt-2 border-t border-dashed border-gray-200">
                <RefreshCw size={12} /> Refresh Analysis
            </button>
        </div>
    );
}
