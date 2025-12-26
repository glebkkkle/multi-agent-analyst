"use client"

import { Card } from "../components/ui/card"
import { Button } from "../components/ui/button"

import {
  ArrowRight,
  Database,
  MessageSquare,
  BarChart3,
  FileSpreadsheet,
  Zap,
  Shield,
  Eye,
  Activity,
  TrendingUp,
  Sparkles,
} from "lucide-react"

const goToLogin = () => {
  window.location.href = "http://localhost:8000/login"
}


export default function LandingPage() {

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm sticky top-0 z-50 bg-background/95">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img 
              src="/icon.svg" 
              alt="Multi-Agent Analyst Logo" 
              className="w-8 h-8"
            />
            <span className="text-xl font-semibold text-foreground">
              Multi-Agent Analyst
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              How it Works
            </a>
            <a href="#transparency" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Transparency
            </a>
            <Button variant="ghost" size="sm" onClick={goToLogin}>
              Sign In
            </Button>

            <Button
              size="sm"
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={goToLogin}
            >
              Get Started
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 md:py-32">
        <div className="max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            Powered by Collaborating AI Agents
          </div>
          <h1 className="text-5xl md:text-7xl font-bold leading-tight">
            Transform raw data into <span className="text-primary">insights</span> in seconds
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Upload your CSV or Excel files and ask questions in plain English. Our multiple AI agents collaborate to
            analyze, visualize, and uncover patterns—no coding required.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Button
              size="lg"
              className="bg-primary text-primary-foreground hover:bg-primary/90 text-base px-8 h-12"
              onClick={goToLogin}
            >
              Start Analyzing
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>

            <Button
              size="lg"
              variant="outline"
              className="text-base px-8 h-12 border-border hover:bg-muted/50"
              onClick={goToLogin}
            >
              View Demo
            </Button>


          </div>

          {/* Visual Demo */}
          <div className="pt-12">
            <Card className="bg-card border-border/50 shadow-2xl overflow-hidden">
              <div className="bg-muted/20 border-b border-border/50 p-4 flex items-center gap-3">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/70" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
                  <div className="w-3 h-3 rounded-full bg-green-500/70" />
                </div>
                <span className="text-sm text-muted-foreground font-mono">analyst.ai/dashboard</span>
              </div>
              <div className="p-8 md:p-12 space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary/15 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1 bg-muted/40 rounded-2xl p-4 border border-border/30">
                    <p className="text-foreground/90">
                      Analyze profit distribution across regions and detect any anomalies
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-4 justify-end">
                  <div className="flex-1 max-w-2xl bg-card/50 border border-primary/20 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center gap-2 text-sm text-primary">
                      <Zap className="w-4 h-4" />
                      <span className="font-medium">3 agents collaborating...</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="space-y-1">
                        <div className="text-3xl font-bold text-foreground">$2.4M</div>
                        <div className="text-xs text-muted-foreground">Total Profit</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-3xl font-bold text-primary">+23%</div>
                        <div className="text-xs text-muted-foreground">Growth</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-3xl font-bold text-red-500">2</div>
                        <div className="text-xs text-muted-foreground">Anomalies</div>
                      </div>
                    </div>
                    <div className="h-32 bg-muted/20 rounded-lg border border-border/30 flex items-center justify-center">
                      <BarChart3 className="w-12 h-12 text-muted-foreground/40" />
                    </div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-primary/15 flex items-center justify-center flex-shrink-0">
                    <img src="/icon.svg" alt="AI" className="w-5 h-5" />
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="container mx-auto px-4 py-20 border-t border-border/30">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-5xl font-bold">Powerful features for modern analytics</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Everything you need to understand your data, without writing a single line of code
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="bg-card border-border/50 p-6 space-y-4 hover:border-primary/30 transition-all">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <FileSpreadsheet className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground">Instant Data Loading</h3>
              <p className="text-muted-foreground leading-relaxed">
                Upload CSV or Excel files and watch them automatically convert to SQL databases. Your data is ready to
                query in seconds.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-6 space-y-4 hover:border-primary/30 transition-all">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground">Natural Language Chat</h3>
              <p className="text-muted-foreground leading-relaxed">
                Ask questions like you would to a colleague. "Show me trends" or "Find outliers"—the AI understands what
                you need.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-6 space-y-4 hover:border-primary/30 transition-all">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Activity className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground">Multi-Agent System</h3>
              <p className="text-muted-foreground leading-relaxed">
                Specialized AI agents collaborate on your query—one loads data, another analyzes, another visualizes.
                Teamwork at machine speed.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-6 space-y-4 hover:border-primary/30 transition-all">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground">Interactive Visualizations</h3>
              <p className="text-muted-foreground leading-relaxed">
                Auto-generated charts, distributions, correlations, and statistical summaries that update in real-time
                as you explore.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-6 space-y-4 hover:border-primary/30 transition-all">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground">Smart Anomaly Detection</h3>
              <p className="text-muted-foreground leading-relaxed">
                AI automatically identifies outliers, unusual patterns, and data quality issues you might miss manually.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-6 space-y-4 hover:border-primary/30 transition-all">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Eye className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground">Complete Transparency</h3>
              <p className="text-muted-foreground leading-relaxed">
                See exactly what each agent did through execution logs and step-by-step reasoning. No black boxes.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="container mx-auto px-4 py-20 border-t border-border/30">
        <div className="max-w-5xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-5xl font-bold">From data to insights in three steps</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Our AI agents work together to deliver comprehensive analysis instantly
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 pt-8">
            <div className="space-y-4 text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto border-2 border-primary/30">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground">Upload Your Data</h3>
              <p className="text-muted-foreground leading-relaxed">
                Drag and drop your CSV or Excel files. We automatically parse and convert them into a queryable SQL
                database.
              </p>
            </div>

            <div className="space-y-4 text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto border-2 border-primary/30">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground">Ask Questions</h3>
              <p className="text-muted-foreground leading-relaxed">
                Type natural language questions. Our agents understand context and collaborate to analyze your data
                intelligently.
              </p>
            </div>

            <div className="space-y-4 text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto border-2 border-primary/30">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground">Get Insights</h3>
              <p className="text-muted-foreground leading-relaxed">
                Receive interactive charts, statistical analysis, and actionable insights—all with full transparency
                into the process.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Transparency Section */}
      <section id="transparency" className="container mx-auto px-4 py-20 border-t border-border/30">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium">
                <Shield className="w-3.5 h-3.5" />
                Built on Trust
              </div>
              <h2 className="text-3xl md:text-5xl font-bold leading-tight">
                See exactly what your AI agents are thinking
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Unlike black-box AI tools, Multi-Agent Analyst shows you every step of the process. Watch agents
                communicate, see their reasoning, and understand exactly how insights were generated.
              </p>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ArrowRight className="w-4 h-4 text-primary" />
                  </div>
                  <span>Full execution logs for every analysis</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ArrowRight className="w-4 h-4 text-primary" />
                  </div>
                  <span>Step-by-step agent reasoning and decisions</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ArrowRight className="w-4 h-4 text-primary" />
                  </div>
                  <span>Complete control over data access and privacy</span>
                </li>
              </ul>
            </div>

            <Card className="bg-card border-border/50 p-6 space-y-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground border-b border-border/30 pb-3">
                <Database className="w-4 h-4" />
                <span className="font-mono">Execution Log</span>
              </div>
              <div className="space-y-3 font-mono text-sm">
                <div className="flex items-start gap-3">
                  <span className="text-primary">Agent-1:</span>
                  <span className="text-muted-foreground">Loading dataset from sales_data.csv...</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-primary">Agent-2:</span>
                  <span className="text-muted-foreground">Analyzing profit distribution by region...</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-primary">Agent-3:</span>
                  <span className="text-muted-foreground">Detecting anomalies using IQR method...</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-primary">Agent-2:</span>
                  <span className="text-muted-foreground">Found 2 outliers in Q3 West region data</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-primary">Agent-4:</span>
                  <span className="text-muted-foreground">Generating interactive visualization...</span>
                </div>
                <div className="flex items-start gap-3 text-primary">
                  <Zap className="w-4 h-4 mt-0.5" />
                  <span>Analysis complete in 2.3s</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Who It's For */}
      <section className="container mx-auto px-4 py-20 border-t border-border/30">
        <div className="max-w-5xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-5xl font-bold">Built for data-driven teams</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Whether you're coding or not, Multi-Agent Analyst fits your workflow
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <Card className="bg-card border-border/50 p-8 space-y-3">
              <h3 className="text-xl font-semibold text-foreground">For Developers & Analysts</h3>
              <p className="text-muted-foreground leading-relaxed">
                Skip repetitive data preprocessing. Export SQL queries and Python code. Maintain full control while
                accelerating your workflow.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-8 space-y-3">
              <h3 className="text-xl font-semibold text-foreground">For Students & Researchers</h3>
              <p className="text-muted-foreground leading-relaxed">
                Learn data analysis concepts through transparent AI reasoning. Perfect for coursework, projects, and
                research without coding barriers.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-8 space-y-3">
              <h3 className="text-xl font-semibold text-foreground">For Business Teams</h3>
              <p className="text-muted-foreground leading-relaxed">
                Make data-driven decisions without waiting for engineering. Ask questions, get answers, and share
                insights in minutes.
              </p>
            </Card>

            <Card className="bg-card border-border/50 p-8 space-y-3">
              <h3 className="text-xl font-semibold text-foreground">For Data Scientists</h3>
              <p className="text-muted-foreground leading-relaxed">
                Prototype analyses rapidly. Validate hypotheses. Let AI handle the grunt work while you focus on complex
                modeling.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 border-t border-border/30">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20 p-12 text-center space-y-6">
            <h2 className="text-3xl md:text-5xl font-bold text-foreground">
              Ready to transform your data?
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Join developers, analysts, and teams who are analyzing data faster with AI agents.
            </p>
              <div className="flex items-center justify-center pt-4">
                <Button
                  size="lg"
                  className="bg-primary text-primary-foreground hover:bg-primary/90 text-base px-8 h-12"
                  onClick={goToLogin}
                >
                  Request Demo
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </div>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/30 mt-20">
        <div className="container mx-auto px-4 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <img 
                  src="/icon.svg" 
                  alt="Multi-Agent Analyst Logo" 
                  className="w-8 h-8"
                />
                <span className="text-lg font-semibold text-foreground">Multi-Agent Analyst</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                AI-powered data analysis through collaborating agents.
              </p>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-foreground">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    API
                  </a>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-foreground">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Contact
                  </a>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-foreground">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Terms
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Security
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-border/30 mt-12 pt-8 text-center text-sm text-muted-foreground">
            <p>© 2025 Multi-Agent Analyst. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}