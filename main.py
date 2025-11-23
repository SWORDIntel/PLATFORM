#!/usr/bin/env python3
"""
SWORD Coder MoE Router - Main Entry Point

Usage:
    python main.py                    # Start router
    python main.py --benchmark        # Run benchmarks
    python main.py --mcp-test         # Test MCP servers
    python main.py --storage          # Show storage estimates
    python main.py --ide              # Launch IDE interface
    python main.py --self-code        # Start interactive self-coding session
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SWORD Coder MoE Router')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmarks')
    parser.add_argument('--mcp-test', action='store_true', help='Test MCP servers')
    parser.add_argument('--storage', action='store_true', help='Show storage estimates')
    parser.add_argument('--ide', action='store_true', help='Launch IDE interface')
    parser.add_argument('--self-code', action='store_true', help='Start self-coding interactive session')
    parser.add_argument('--workspace', default=os.getcwd(), help='Workspace root directory')
    parser.add_argument('--host', default='0.0.0.0', help='Router host')
    parser.add_argument('--port', type=int, default=8000, help='Router port')
    args = parser.parse_args()

    if args.benchmark:
        print("Running benchmarks...")
        os.system(f'{sys.executable} scripts/benchmark_router.py')
        return

    if args.mcp_test:
        print("Testing MCP servers...")
        from mcp_router import create_mcp_enhanced_router
        create_mcp_enhanced_router()
        return

    if args.storage:
        print("Storage Estimates:")
        print("=" * 60)
        from quantization_pipeline import QuantizationPipeline
        pipeline = QuantizationPipeline()
        storage = pipeline.estimate_total_storage(quantization="int4")
        print(f"Total FP32: {storage['total_fp32_gb']:.1f} GB ({storage['total_fp32_gb']/1024:.2f} TB)")
        print(f"Total INT4: {storage['total_quantized_gb']:.1f} GB")
        print(f"Savings:    {storage['total_savings_gb']:.1f} GB")
        print(f"Compression: {storage['average_compression']:.1f}x")
        print()
        print("Per-model breakdown:")
        for model, info in storage['models'].items():
            print(f"  {model:<35} {info['fp32_gb']:>6.1f} GB -> {info['quantized_gb']:>5.2f} GB ({info['compression_ratio']:.1f}x)")
        return

    if args.ide:
        print("=" * 60)
        print("SWORD Self-Coding IDE")
        print("=" * 60)
        print(f"Workspace: {args.workspace}")
        print("Launching IDE interface...")
        print()
        from ide_interface import run_ide
        run_ide(args.workspace)
        return

    if args.self_code:
        print("=" * 60)
        print("SWORD Self-Coding Agent - Interactive Session")
        print("=" * 60)
        print(f"Workspace: {args.workspace}")
        print()
        from self_coder import SelfCodingAgent
        agent = SelfCodingAgent(args.workspace)
        agent.interactive_session()
        return

    # Start router
    print("=" * 60)
    print("SWORD Coder MoE Router")
    print("=" * 60)
    print(f"Host: {args.host}:{args.port}")
    print()

    os.environ['ROUTER_HOST'] = args.host
    os.environ['ROUTER_PORT'] = str(args.port)

    import uvicorn
    from generic_router import app

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
