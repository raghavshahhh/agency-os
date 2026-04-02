#!/usr/bin/env python3
"""
RAGSPRO Expert Agent Dashboard
Unified interface for managing all expert agents
Marketing Agent manages everything from here
"""

import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from agents import AgentOrchestrator, AgentRole

st.set_page_config(
    page_title="Agent Command Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize orchestrator
@st.cache_resource
def get_orchestrator():
    orch = AgentOrchestrator()
    orch.initialize_agents()
    return orch

orchestrator = get_orchestrator()

# ─── HEADER ─────────────────────────────────────────────────────────────────

st.title("🤖 RAGSPRO Expert Agent Command Center")
st.markdown("AI-powered marketing automation with expert agents that collaborate")

# ─── AGENT STATUS OVERVIEW ─────────────────────────────────────────────────

st.header("👥 Expert Agent Team")

agents_data = orchestrator.get_all_status()

# Display agents in a grid
cols = st.columns(len(agents_data))

for idx, (agent_id, agent_info) in enumerate(agents_data.items()):
    with cols[idx]:
        st.markdown(f"### {agent_info['avatar']} {agent_info['name']}")

        # Status indicator
        status_colors = {
            "active": "🟢",
            "idle": "⚪",
            "error": "🔴",
            "busy": "🟡"
        }
        status_emoji = status_colors.get(agent_info['status'], "⚫")

        st.markdown(f"{status_emoji} **{agent_info['status'].upper()}**")
        st.caption(f"*{agent_info['role'].upper()}*")

        # Stats
        st.metric("Ideas", agent_info['ideas_generated'])
        st.metric("Tasks", agent_info['tasks_completed'])

        # Expertise tags
        for exp in agent_info['expertise']:
            st.caption(f"• {exp}")

        # Action button
        if st.button(f"💬 Message {agent_info['name']}", key=f"msg_{agent_id}"):
            st.session_state['selected_agent'] = agent_id
            st.rerun()

# ─── MARKETING AGENT CONTROL CENTER ─────────────────────────────────────────

st.divider()
st.header("🎯 Marketing Agent - Control Center")

marketing_col1, marketing_col2, marketing_col3 = st.columns(3)

with marketing_col1:
    st.markdown("### Content Generation")

    platform = st.selectbox(
        "Platform",
        ["Instagram", "LinkedIn", "Twitter/X", "YouTube"],
        key="content_platform"
    )

    content_type = st.selectbox(
        "Content Type",
        ["carousel", "reel", "post", "thread", "article", "video"],
        key="content_type"
    )

    topic = st.text_input("Topic (optional)", placeholder="AI automation", key="content_topic")

    if st.button("🚀 Generate Content", use_container_width=True):
        with st.spinner(f"{agents_data['content_agent']['name']} is creating content..."):
            marketing_agent = orchestrator.get_agent("marketing_agent")
            if marketing_agent:
                marketing_agent.request_content_creation(
                    platform.lower(),
                    content_type,
                    topic if topic else None
                )
                st.success(f"✅ Content request sent to {agents_data['content_agent']['name']}!")

with marketing_col2:
    st.markdown("### Market Research")

    research_type = st.selectbox(
        "Research Focus",
        ["Trending Topics", "Competitor Analysis", "Content Gaps"],
        key="research_type"
    )

    if st.button("🔍 Start Research", use_container_width=True):
        with st.spinner(f"{agents_data['research_agent']['name']} is researching..."):
            marketing_agent = orchestrator.get_agent("marketing_agent")
            if marketing_agent:
                research_map = {
                    "Trending Topics": "trends",
                    "Competitor Analysis": "competitor_analysis",
                    "Content Gaps": "content_gaps"
                }
                marketing_agent.request_market_research(research_map.get(research_type))
                st.success(f"✅ Research request sent!")

with marketing_col3:
    st.markdown("### Posting & Scheduling")

    queue_data = orchestrator.get_agent("posting_agent")
    if queue_data:
        queue = queue_data.get_content_queue()
        st.metric("Scheduled Posts", len(queue))

    if st.button("📤 View Content Queue", use_container_width=True):
        st.session_state['view_queue'] = True
        st.rerun()

    if st.button("📊 Business Report", use_container_width=True):
        st.session_state['view_business'] = True
        st.rerun()

# ─── CONTENT QUEUE VIEWER ──────────────────────────────────────────────────

if st.session_state.get('view_queue'):
    st.divider()
    st.subheader("📋 Content Queue")

    posting_agent = orchestrator.get_agent("posting_agent")
    if posting_agent:
        queue = posting_agent.get_content_queue()

        if queue:
            for item in queue:
                with st.expander(f"{item['platform'].upper()} - {item['content'].get('content_type', 'post')}"):
                    st.json(item)
        else:
            st.info("No scheduled content in queue")

    if st.button("Close Queue"):
        del st.session_state['view_queue']
        st.rerun()

# ─── BUSINESS INTELLIGENCE ──────────────────────────────────────────────────

if st.session_state.get('view_business'):
    st.divider()
    st.subheader("💼 Business Intelligence")

    business_agent = orchestrator.get_agent("business_agent")
    if business_agent:
        dashboard_data = business_agent.get_dashboard_data()

        biz_cols = st.columns(4)
        with biz_cols[0]:
            st.metric("Revenue Progress", dashboard_data['business_summary']['revenue_progress'])
        with biz_cols[1]:
            st.metric("Current Revenue", dashboard_data['business_summary']['current_revenue'])
        with biz_cols[2]:
            st.metric("Active Opportunities", dashboard_data['active_opportunities'])
        with biz_cols[3]:
            st.metric("Healthy Agents", dashboard_data['agent_health_summary']['healthy'])

        # Services
        st.markdown("### Services Offered")
        for service in dashboard_data['services']:
            st.caption(f"**{service['name']}** - ₹{service['price']:,}")
            st.caption(f"_{service['description']}_")

        # Metrics
        st.markdown("### Performance Metrics")
        st.json(dashboard_data['metrics'])

    if st.button("Close Business View"):
        del st.session_state['view_business']
        st.rerun()

# ─── AGENT COMMUNICATION ───────────────────────────────────────────────────

st.divider()
st.header("💬 Agent Communications")

dashboard_data = orchestrator.get_dashboard_data()
recent_messages = dashboard_data.get('recent_messages', [])

if recent_messages:
    for msg in reversed(recent_messages[-5:]):
        with st.container():
            cols = st.columns([1, 3])
            with cols[0]:
                st.markdown(f"**{msg['from_agent']}** →")
                st.caption(msg['timestamp'][:16])
            with cols[1]:
                st.markdown(f"*{msg['message_type'].upper()}*")
                st.write(msg['content'])
else:
    st.info("No recent communications")

# ─── UNIFIED CONTENT DASHBOARD ──────────────────────────────────────────────

st.divider()
st.header("📝 Content Dashboard - All Platforms")

content_tabs = st.tabs(["Instagram", "LinkedIn", "Twitter/X", "YouTube"])

platforms = ["instagram", "linkedin", "twitter", "youtube"]

for tab, platform in zip(content_tabs, platforms):
    with tab:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"### 📱 {platform.upper()} Content")

            # Quick content creation
            content_col = st.columns(2)
            with content_col[0]:
                if platform == "instagram":
                    if st.button("📸 Create Carousel", key=f"ig_car_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "carousel")
                            st.success("Carousel queued!")
                            st.rerun()
                    if st.button("🎬 Create Reel", key=f"ig_reel_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "reel")
                            st.success("Reel queued!")
                            st.rerun()

                elif platform == "linkedin":
                    if st.button("📄 Create Post", key=f"li_post_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "post")
                            st.success("Post queued!")
                            st.rerun()
                    if st.button("📰 Create Article", key=f"li_art_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "article")
                            st.success("Article queued!")
                            st.rerun()

                elif platform == "twitter":
                    if st.button("💬 Create Thread", key=f"tw_thread_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "thread")
                            st.success("Thread queued!")
                            st.rerun()
                    if st.button("🐦 Create Tweet", key=f"tw_tweet_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "post")
                            st.success("Tweet queued!")
                            st.rerun()

                elif platform == "youtube":
                    if st.button("🎥 Create Video Script", key=f"yt_vid_{platform}"):
                        marketing_agent = orchestrator.get_agent("marketing_agent")
                        if marketing_agent:
                            marketing_agent.request_content_creation(platform, "video")
                            st.success("Video script queued!")
                            st.rerun()

        with col2:
            st.markdown("### 📊 Stats")
            # Show platform stats from posting agent
            posting_agent = orchestrator.get_agent("posting_agent")
            if posting_agent:
                dashboard = posting_agent.get_dashboard_data()
                posts_by_platform = dashboard.get('posting_stats', {}).get('by_platform', {})
                st.metric(f"{platform.title()} Posts", posts_by_platform.get(platform, 0))

# ─── SYSTEM STATUS ───────────────────────────────────────────────────────────

st.divider()
st.header("🔧 System Status")

sys_col1, sys_col2, sys_col3 = st.columns(3)

with sys_col1:
    st.metric("Total Agents", dashboard_data['system_status']['total_agents'])

with sys_col2:
    st.metric("Active Agents", dashboard_data['system_status']['active_agents'])

with sys_col3:
    st.metric("System Status", "🟢 RUNNING" if dashboard_data['system_status']['running'] else "⚪ IDLE")

# ─── FOOTER ─────────────────────────────────────────────────────────────────

st.divider()
st.caption("RAGSPRO Expert Agent System | Agents communicate and collaborate automatically | Built with 💪 by Raghav")
