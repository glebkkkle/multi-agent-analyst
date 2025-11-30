import io
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import numpy as np
from langchain_core.tools import StructuredTool

from src.multi_agent_analyst.schemas.visualization_agent_schema import (
    PieChartSchema,
    TableVisualizationSchema,
)

from src.multi_agent_analyst.utils.utils import object_store

plt.rcParams.update({
    "figure.facecolor": "#050508",
    "axes.facecolor": "#0c0c11",
    "savefig.facecolor": "#050508",
    "axes.edgecolor": "#6366f1",
    "text.color": "#e5e7eb",
    "axes.labelcolor": "#e5e7eb",
    "xtick.color": "#d1d5db",
    "ytick.color": "#d1d5db",
    "font.family": "Inter",
    "axes.titleweight": "bold",
    "axes.titlecolor": "#ffffff",
})

COLORS = {
    'background': '#060b16',       # deep navy
    'panel':      '#0d1526',       # slightly lighter navy
    'primary':    '#3b82f6',       # blue-500
    'accent':     '#60a5fa',       # blue-400
    'grid':       '#1e293b',       # slate-800
    'text':       '#e2e8f0',       # slate-200
}


def setup_plot_style(fig, ax):
    # FIGURE BACKGROUND
    fig.patch.set_facecolor(COLORS['background'])
    ax.set_facecolor(COLORS['panel'])

    # GRID
    ax.grid(
        True,
        linestyle='--',
        linewidth=0.7,
        color=COLORS['grid'],
        alpha=0.25
    )

    # SPINES
    for spine in ax.spines.values():
        spine.set_color(COLORS['grid'])
        spine.set_linewidth(1.2)

    # TICKS
    ax.tick_params(
        colors=COLORS['text'],
        labelsize=10,
        length=6,
        width=1
    )

    # LABEL COLORS
    ax.xaxis.label.set_color(COLORS['text'])
    ax.yaxis.label.set_color(COLORS['text'])

    # TITLE
    ax.title.set_color(COLORS['text'])
    ax.title.set_weight('bold')

    # ENSURE EXPORT BG MATCHES
    plt.rcParams['savefig.facecolor'] = COLORS['background']


def make_scatter_plot_tool(df):
    """Beautiful scatter plot with gradient colors and styling."""

    def scatter_plot():
        numeric_cols = df.select_dtypes(include=['float', 'int']).columns

        if len(numeric_cols) < 2:
            raise ValueError("Not enough numeric columns for scatter plot.")

        x_col, y_col = numeric_cols[:2]

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7), dpi=100)
        
        # Create gradient colors based on y values
        colors = df[y_col]
        
        # Scatter plot with beautiful styling
        scatter = ax.scatter(
            df[x_col], 
            df[y_col],
            c=colors,
            cmap='viridis',
            s=150,  # Larger points
            alpha=0.8,
            edgecolors=COLORS['primary'],
            linewidth=2
        )
        
        # Add colorbar with styling
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.ax.set_ylabel(y_col, rotation=270, labelpad=20, color='#e8e8f0', fontsize=11, weight='bold')
        cbar.ax.tick_params(colors='#c8c8d8')
        cbar.outline.set_edgecolor(COLORS['primary'])
        cbar.outline.set_linewidth(1.5)
        cbar.outline.set_alpha(0.3)
        
        # Set labels with title
        ax.set_xlabel(x_col, fontsize=12, weight='bold')
        ax.set_ylabel(y_col, fontsize=12, weight='bold')
        ax.set_title(f'{y_col} vs {x_col}', 
                    fontsize=16, 
                    weight='bold', 
                    color='#e8e8f0',
                    pad=20)
        
        # Apply modern styling
        setup_plot_style(fig, ax)
        
        # Add subtle shadow effect
        ax.add_patch(Rectangle((0, 0), 1, 1,
                              transform=ax.transAxes,
                              facecolor='none',
                              edgecolor=COLORS['primary'],
                              linewidth=2,
                              alpha=0.2))
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight', facecolor=COLORS['background'], dpi=100)
        # svg=buf.getvalue()
        # print(svg)
        buf.seek(0)
        plt.close()

        return object_store.save(buf)

    return StructuredTool.from_function(
        func=scatter_plot,
        name="scatter_plot",
        description="Beautiful scatter plot with gradient colors based on numeric columns.",
        args_schema=TableVisualizationSchema,
    )


def make_line_plot_tool(df):
    """Elegant line plot with smooth curves and beautiful styling."""
    
    def line_plot():
        try:
            # Find date column
            date_col = None
            for col in df.columns:
                if "date" in col.lower():
                    date_col = col
                    break

            if date_col is None:
                raise ValueError("Line plot requires a date column.")

            # Choose first numeric column
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric column to plot.")

            y_col = numeric_cols[0]

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
            
            # Plot line with gradient effect
            x_data = range(len(df))
            y_data = df[y_col].values
            
            # Main line
            line = ax.plot(x_data, y_data, 
                          color=COLORS['primary'],
                          linewidth=3,
                          label=y_col,
                          zorder=3)
            
            # Add markers
            ax.scatter(x_data, y_data,
                      color=COLORS['accent'],
                      s=100,
                      alpha=0.9,
                      edgecolors='white',
                      linewidth=2,
                      zorder=4)
            
            ax.fill_between(
                x_data,
                y_data,
                color=COLORS['primary'],
                alpha=0.12
            )
            
            # Set labels
            ax.set_xlabel('Date', fontsize=12, weight='bold')
            ax.set_ylabel(y_col, fontsize=12, weight='bold')
            ax.set_title(f'{y_col} Over Time', 
                        fontsize=16, 
                        weight='bold', 
                        color='#e8e8f0',
                        pad=20)
            
            # Format x-axis with dates
            ax.set_xticks(x_data[::max(1, len(x_data)//10)])
            ax.set_xticklabels(df[date_col].iloc[::max(1, len(df)//10)], 
                              rotation=45, 
                              ha='right')
            
            # Apply modern styling
            setup_plot_style(fig, ax)
            
            # Add legend
            ax.legend(loc='upper left', 
                     framealpha=0.9,
                     facecolor='#1a1625',
                     edgecolor=COLORS['primary'],
                     fontsize=10,
                     labelcolor='#e8e8f0')
            
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches='tight', facecolor=COLORS['background'], dpi=100)
            buf.seek(0)
            plt.close()
            
        except Exception as e:
            return {'exception': e}
            
        return object_store.save(buf)

    return StructuredTool.from_function(
        func=line_plot,
        name="line_plot",
        description="Elegant line plot with smooth curves and gradient fill.",
        args_schema=TableVisualizationSchema,
    )


def make_pie_chart_tool(df):
    """Modern pie chart with beautiful gradients and styling."""

    def pie_chart(column_names: list):
        try:
            values = df.iloc[0].tolist() if len(df) > 0 else []
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
            fig.patch.set_facecolor(COLORS['background'])
            ax.set_facecolor(COLORS['background'])
            
            # Create gradient colors
            colors_list = [COLORS['gradient'][i % len(COLORS['gradient'])] for i in range(len(values))]
            
            # Create pie chart with explosion effect
            explode = [0.05] * len(values)  # Slightly separate all slices
            
            wedges, texts, autotexts = ax.pie(
                values,
                labels=column_names,
                colors=colors_list,
                explode=explode,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': '#e8e8f0', 'fontsize': 11, 'weight': 'bold'},
                wedgeprops={'edgecolor': COLORS['background'], 'linewidth': 3, 'antialiased': True}
            )
            
            # Style the percentage text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_weight('bold')
            
            # Style the labels
            for text in texts:
                text.set_color('#e8e8f0')
                text.set_fontsize(11)
                text.set_weight('bold')
            
            # Add title
            ax.set_title('Distribution', 
                        fontsize=16, 
                        weight='bold', 
                        color='#e8e8f0',
                        pad=20)
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches='tight', facecolor=COLORS['background'], dpi=100)
            buf.seek(0)
            plt.close()
            
        except Exception as e:
            return {'exception': e}

        return object_store.save(buf)

    return StructuredTool.from_function(
        func=pie_chart,
        name="pie_chart",
        description="Modern pie chart with gradient colors and elegant styling.",
        args_schema=PieChartSchema,
    )


def make_bar_chart_tool(df):
    """Beautiful bar chart with gradients and modern styling."""

    def bar_chart():
        try:
            # Get first categorical and first numeric column
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            num_cols = df.select_dtypes(include=['float', 'int']).columns
            
            if len(cat_cols) == 0 or len(num_cols) == 0:
                raise ValueError("Need at least one categorical and one numeric column")
            
            cat_col = cat_cols[0]
            num_col = num_cols[0]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 7), dpi=100)
            
            # Create gradient colors
            n_bars = len(df)
            colors_list = plt.cm.viridis(np.linspace(0.3, 0.9, n_bars))
            
            # Create bars
            bars = ax.bar(range(len(df)), df[num_col], 
                          color=colors_list,
                          edgecolor=COLORS['primary'],
                          linewidth=2,
                          alpha=0.9)
            
            # Add value labels on top of bars
            for i, (bar, value) in enumerate(zip(bars, df[num_col])):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.0f}',
                       ha='center', va='bottom',
                       color='#e8e8f0',
                       fontsize=10,
                       weight='bold')
            
            # Set labels
            ax.set_xlabel(cat_col, fontsize=12, weight='bold')
            ax.set_ylabel(num_col, fontsize=12, weight='bold')
            ax.set_title(f'{num_col} by {cat_col}',
                        fontsize=16,
                        weight='bold',
                        color='#e8e8f0',
                        pad=20)
            
            # Set x-axis labels
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df[cat_col], rotation=45, ha='right')
            
            # Apply modern styling
            setup_plot_style(fig, ax)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches='tight', facecolor=COLORS['background'], dpi=100)
            buf.seek(0)
            plt.close()
            
        except Exception as e:
            return {'exception': e}
        
        return object_store.save(buf)
    
    return StructuredTool.from_function(
        func=bar_chart,
        name="bar_chart",
        description="Beautiful bar chart with gradient colors.",
        args_schema=TableVisualizationSchema,
    )


def make_table_visualization_tool(df):
    """Factory: returns a table visualization tool bound to the given dataframe."""

    def table_visualization():
        return object_store.save(df)

    return StructuredTool.from_function(
        func=table_visualization,
        name="table_visualization",
        description="Stores the DataFrame as an object and returns its ID.",
        args_schema=TableVisualizationSchema,
    )


__all__ = [
    "make_line_plot_tool",
    "make_scatter_plot_tool",
    "make_pie_chart_tool",
    "make_bar_chart_tool",
    "make_table_visualization_tool",
]